#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Jul 10 16:30:16 2020

@author: filip

An tkinter implementation for particle counting.
"""

import os
import numpy as np
import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk, ImageFilter, ImageOps
from tkinter import filedialog
from tkinter import messagebox
from skimage import io
from skimage.morphology import closing, square, binary_erosion, binary_dilation, binary_closing, binary_opening
from skimage.measure import label, regionprops
from skimage.filters import gaussian, median
from skimage.color import rgb2gray
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import matplotlib.pyplot as plt


class SelectionForm(tk.LabelFrame):
    
    def __init__(self, master, command):
        super().__init__(master, text="Filters")
        
        self.update_canvas = command
        
        self.gauss_var = tk.StringVar()
        select_label = tk.Label(self, text="Gaussian blur")
        self.selection = tk.Spinbox(self, from_=0, to=100, width=5,
                                    command=command, textvariable = self.gauss_var)
        
        self.median_var = tk.StringVar()
        median_label = tk.Label(self, text="Median blur")
        self.median = tk.Spinbox(self, from_=1, to=11, increment=2, width=5, 
                                 command=command, textvariable = self.median_var)
        
        self.thres_var = tk.StringVar()
        thresh_label = tk.Label(self, text="Threshold")
        self.thresh = tk.Spinbox(self, from_=0, to=255,
                                 increment=2, width=5, command=command,
                                 textvariable=self.thres_var)
        
        self.undo_thresh_btn = tk.Button(self, text="Undo",
                                    command=self.reset_threshold)
        
        select_label.grid(sticky=tk.W, row=0, column=0)
        self.selection.grid(row=0, column=1, pady=10)
        median_label.grid(sticky=tk.W, row=1, column=0)
        self.median.grid(row=1, column=1, pady=10)
        thresh_label.grid(sticky=tk.W, row=2, column=0)
        self.thresh.grid(row=2, column=1, pady=10)
        self.undo_thresh_btn.grid(row=3, column=0, pady=10, columnspan=2)
        
        self.settings = None
        
    def get_selection(self):
        return int(self.selection.get())

    def get_median(self):
        return int(self.median.get())
    
    def get_threshold(self):
        return int(self.thresh.get())
    
    def reset_threshold(self):
        if not self.settings:
            self.settings = int(self.get_selection()), int(self.get_median()), int(self.get_threshold())
            self.thres_var.set(0)
            self.gauss_var.set(0)
            self.median_var.set(1)
            self.undo_thresh_btn.config(text="Redo")
        else:
            self.thres_var.set(self.settings[2])
            self.gauss_var.set(self.settings[0])
            self.median_var.set(self.settings[1])
            self.settings = None
            self.undo_thresh_btn.config(text="Undo")
        self.update_canvas()

class Filters2Form(tk.LabelFrame):

    def __init__(self, master, update_canvas):
        super().__init__(master, text="Filters 2")
        
        self.update_canvas = update_canvas
        erosion_btn = tk.Button(self, text="Erosion", command=self.add_erosion)
        self.erosion = tk.Spinbox(self, from_=2, to=10, width=5)
        
        dilation_btn = tk.Button(self, text="Dilation", command=self.add_dilation)
        self.dilation = tk.Spinbox(self, from_=2, to=10, width=5)
        
        opening_btn = tk.Button(self, text="Opening", command=self.add_opening)
        self.opening = tk.Spinbox(self, from_=2, to=10, width=5)
        
        closing_btn = tk.Button(self, text="Closing", command=self.add_closing)
        self.closing = tk.Spinbox(self, from_=2, to=10, width=5)
        
        undo_btn = tk.Button(self, text="Undo",
                             command=self.undo)
        
        self.filters_list = tk.Listbox(self, height=5)
        list_scroll = tk.Scrollbar(self, orient=tk.VERTICAL,
                                   command=self.filters_list.yview)
        self.filters_list.config(yscrollcommand=list_scroll.set)
        
        erosion_btn.grid(sticky=tk.W, row=0, column=0)
        self.erosion.grid(row=0, column=1, pady=10, padx=5)
        dilation_btn.grid(sticky=tk.W, row=1, column=0)
        self.dilation.grid(row=1, column=1, pady=10, padx=5)
        opening_btn.grid(sticky=tk.W, row=2, column=0)
        self.opening.grid(row=2, column=1, pady=10, padx=5)
        closing_btn.grid(sticky=tk.W, row=3, column=0)
        self.closing.grid(row=3, column=1, pady=10, padx=5)
        undo_btn.grid(row=4,column=0, columnspan=2, pady=10)
        self.filters_list.grid(row=5, column=0, columnspan=2)
        list_scroll.grid(row=5, column=1, sticky='nse')
        
        self.filters = []
        
    def add_erosion(self):
        self.filters.append(('ero', int(self.erosion.get())))
        self.update_canvas()
        self.filters_list.insert(tk.END, f"Erosion: {self.erosion.get()}")
        self.filters_list.see(tk.END)
    
    def add_dilation(self):
        self.filters.append(('dil', int(self.dilation.get())))
        self.update_canvas()
        self.filters_list.insert(tk.END, f"Dilation: {self.dilation.get()}")
        self.filters_list.see(tk.END)
        
    def add_opening(self):
        self.filters.append(('ope', int(self.opening.get())))
        self.update_canvas()
        self.filters_list.insert(tk.END, f"Opening: {self.opening.get()}")
        self.filters_list.see(tk.END)
        
    def add_closing(self):
        self.filters.append(('clo', int(self.closing.get())))
        self.update_canvas()
        self.filters_list.insert(tk.END, f"Closing: {self.closing.get()}")
        self.filters_list.see(tk.END)
        
    def undo(self):
        self.filters_list.delete(0,tk.END)
        self.filters = []
        self.update_canvas()
        
    def get_filters(self):
        return self.filters
  
class BottomMenu(ttk.Frame):
    def __init__(self, master, update_canvas, count_cmd, extract_cmd, **kwargs):
        super().__init__(master, **kwargs)
        self.update_canvas = update_canvas
        
        self.btn = tk.Button(self, text="Load directory",
                             command=self.load_image_paths)
        self.count_btn = tk.Button(self, text="Count",
                                   command=count_cmd)
        
        self.prev_photo_btn = tk.Button(self, text="<",
                                        command=self.prev_photo)
        self.next_photo_btn = tk.Button(self, text=">",
                                        command=self.next_photo)
        self.extract_btn = tk.Button(self, text="Extract",
                                     command=extract_cmd, width=30)
        
        self.image_label = tk.Label(self, text="Image path placeholder")
        self.war_label = tk.Label(self, text="")
        
        self.btn.grid(row=0, column=0)
        self.count_btn.grid(row=0, column=1)
        self.prev_photo_btn.grid(row=0, column=2)
        self.next_photo_btn.grid(row=0, column=3)
        self.extract_btn.grid(row=0, column=4, sticky="ne")
        self.war_label.grid(row=1, column=0, columnspan=2, sticky="nw")
        self.image_label.grid(row=1, column=4, sticky="e")
        self.columnconfigure(4, weight=1)
        
        self.input_folder = None
        self.output_folder = None
        self.image_paths = []
        self.image_selected = 0
        
    def load_image_paths(self):
        self.input_folder = filedialog.askdirectory()
        self.image_paths = os.listdir(self.input_folder)
        self.image_paths = [os.path.join(self.input_folder.split("/")[-1], image_path) for image_path in self.image_paths]
        self.image_paths.sort()
        self.image_label.config(text=self.get_image_path())
        self.update_canvas()
    
    def next_photo(self):
        if self.image_paths:
            self.image_selected += 1
        if self.image_selected >= len(self.image_paths):
            self.image_selected = len(self.image_paths) - 1
        self.image_label.config(text=self.get_image_path())
        self.update_canvas()
        
    def prev_photo(self):
        if self.image_paths:
            self.image_selected -= 1
        if self.image_selected < 0:
            self.image_selected = 0
        self.image_label.config(text=self.get_image_path())
        self.update_canvas()
                    
    def get_image_path(self):
        return self.image_paths[self.image_selected]
    
    def too_many_particles_warning(self):
        if self.war_label['text'] == "":
            self.war_label.config(text="Warning! Too many particles!", fg='red')
            self.after(2000, self.too_many_particles_warning)
        else:
            self.war_label.config(text="")
            
    def get_output_folder(self):
        if not self.output_folder:
            self.output_folder = tk.filedialog.askdirectory()
        return self.output_folder
        
        
class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Particle Counter 0.1")
        
        filters_frame = tk.Frame(self)
        self.form = SelectionForm(filters_frame, command=self.update_canvas)
        self.form2 = Filters2Form(filters_frame, 
                                  update_canvas=self.update_canvas)
        
        self.form.grid(row=0,column=0)
        self.form2.grid(row=1,column=0)
        
        self.canvas = tk.Canvas(self, bg="black",
                                width=int(self.winfo_width()),
                                height=self.winfo_height())
        
        self.bottom_menu = BottomMenu(self, self.update_canvas, self.label_image,
                                      self.extract_images)
        
        self.count = tk.StringVar()
        self.count_label = tk.Label(self, text="Particles")
        self.count_box = tk.Entry(self, width = 10, state="readonly",
                                  textvariable=self.count)
        
        filters_frame.grid(row=0, column=0, padx=10, pady=10)
        filters_frame.columnconfigure(0, minsize=100)
        # self.count_label.grid(row=2, column=0)
        self.count_box.grid(row=1, column=0)
        self.canvas.grid(row=0, column=1, sticky="nswe")
        self.bottom_menu.grid(row=1, column=1, sticky="we")
        
        self.bind("<Configure>", self.resize) # Maybe the setting can be changed dinamically when window is changed
        self.bind("<Return>", self.update_canvas)
        self.bind("<KP_Enter>", self.update_canvas)
        self.update_idletasks()
        self.minsize(800, 600)

        #######################################
        # IMAGES
        # Three phases = Orig, Thresh, Eroded/Dilated
        #######################################
        self.image = None
        self.image_filter1 = None
        self.filtered_image = None
        #######################################
        # ROI LIST
        #######################################
        self.roi = []
             
    def update_canvas(self, *args):
        self.load_image()
        image = self.threshold_image(self.image)
        self.filtered_image = self.apply_filters2(image)
        image = Image.fromarray(self.filtered_image)
        self.canvas.delete("all")
        self.canvas_image = ImageTk.PhotoImage(image)
        self.canvas.create_image(0,0, anchor=tk.NW, image=self.canvas_image)
               
    def resize(self, event):
        # region = self.canvas.bbox(tk.ALL)
        self.canvas.configure(height=self.winfo_height()-50,
                              width=self.winfo_width()-170)

    def load_image(self):
        self.image = rgb2gray(io.imread(self.bottom_menu.get_image_path())[:,:,:3]) * 255
            
    def threshold_image(self, image):
        image = gaussian(image, self.form.get_selection())
        image = median(image, square(self.form.get_median()))
        if self.form.get_threshold():
            image = closing(image > self.form.get_threshold(), square(1))
        return image      
    
    def apply_filters2(self, image):
        if self.form2.get_filters():
            for opp, val in self.form2.get_filters():
                if opp == 'ero':
                    image = binary_erosion(image, footprint=square(val))
                elif opp == 'dil':
                    image = binary_dilation(image, footprint=square(val))
                elif opp == 'ope':
                    image = binary_opening(image, footprint=square(val))
                elif opp == 'clo':
                    image = binary_closing(image, footprint=square(val))
            return image
        return image
            
    def extract_images(self):
        output_folder = self.bottom_menu.get_output_folder()
        if type(self.filtered_image) == np.ndarray:
            label_image = label(self.filtered_image)
            image_name = self.bottom_menu.get_image_path().split("/")[-1].split(".")[0]
            # Generate folders if they don't exist
            images_output_path = os.path.join(output_folder, 'extracted', image_name, 'images')
            masks_output_path = os.path.join(output_folder, 'extracted', image_name, 'masks')
            if not os.path.exists(images_output_path):
                os.makedirs(images_output_path)
            if not os.path.exists(masks_output_path):
                os.makedirs(masks_output_path)
            io.imsave(os.path.join(images_output_path, f'{image_name}.png'), self.image)
            for i in range(np.max(label_image)):
                io.imsave(os.path.join(masks_output_path, f'{image_name}-{i+1}.png'), np.where(label_image==i+1, 1, 0))
                
    
    def label_image(self):
        self.roi = []
        if type(self.image) == np.ndarray:
            image = np.asarray(self.filtered_image)
            label_image = label(image)
            
            if label_image.max() < 500:
                for region in regionprops(label_image):
                    # take regions with large enough areas
                    if region.area:
                        # draw rectangle around segmented coins
                        minr, minc, maxr, maxc = region.bbox
                        self.roi.append([minc, minr, maxc, maxr])
                self.update_canvas()
                
            else:
                self.war_label.config(text="Warning! Too many particles!")
            self.count.set(label_image.max())
        
        for roi in self.roi:
            rectangle = roi
            self.canvas.create_rectangle(*rectangle, outline='red', 
                                          width=1)


if __name__ == "__main__":
    app = App()
    app.mainloop()
