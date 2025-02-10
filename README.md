
Python Intensity Multi-Channel Profile Analyser (PyIMPA)
======================================

**Python Intensity Multi-Channel Profile Analyser (PyIMPA)** is a scientific imaging tool written in Python that enables researchers to perform precise intensity profile analysis on both RGB and grayscale images. With an intuitive graphical user interface (GUI) built with PyQt5, PyIMPA allows users to load images, define regions of interest (ROI) by drawing line segments, extract intensity profiles, and visualize detailed cross-sectional (“band”) information. The software supports multi-channel analysis, customizable chart styling, and preset saving/loading, making it ideal for applications in microscopy, medical imaging, materials science, and other research fields requiring quantitative image analysis.

* * *

Table of Contents
-----------------

*   [Features](#features)
*   [Installation](#installation)
*   [Usage](#usage)
*   [Software Architecture and Code Structure](#software-architecture-and-code-structure)
*   [Intensity Profile and Band Extraction Algorithm](#intensity-profile-and-band-extraction-algorithm)
*   [Scientific Applications](#scientific-applications)
*   [Customization and Presets](#customization-and-presets)
*   [Future Improvements](#future-improvements)
*   [License](#license)
*   [Contributing](#contributing)
*   [Acknowledgments](#acknowledgments)

* * *

Features
--------

*   **Image Loading and Display**
    *   Supports common image formats (PNG, JPEG, BMP, TIFF, etc.)
    *   Displays images at their native resolution in a scrollable view for precise analysis.
*   **Multi-Channel Support**
    *   Works with both RGB and grayscale images.
    *   Enables extraction of individual channels (Red, Green, Blue) or a computed grayscale (average).
*   **ROI and Segment Definition**
    *   Draw segments directly on the image by selecting two points.
    *   Supports manual coordinate entry for precise segment placement.
    *   Visual feedback with overlaid handles and lines drawn on the image.
*   **Band Extraction and Preview**
    *   Extracts a rectified “band” (cross-sectional profile) perpendicular to the drawn segment.
    *   Displays a band preview showing the extracted cross-section of intensity values.
*   **Intensity Profile Calculation**
    *   Computes mean intensity values along the defined segment.
    *   Supports binning of intensity values and plots standard deviation (error bars) for quantitative analysis.
    *   Provides multi-channel profile plots to compare channel-specific intensity distributions.
*   **Visualization Tools**
    *   Two magnifier windows provide zoomed-in views around the selected endpoints.
    *   A separate visualization window can be opened for a consolidated view of the image, magnifiers, and band preview.
*   **Preset Saving and Loading**
    *   Save analysis and chart styling options to a JSON file.
    *   Load saved presets to quickly reapply previous configurations.

* * *

Installation
------------

### Prerequisites

*   **Python 3.6+**
*   **pip**

### Dependencies

Install the required Python packages using pip:

    pip install numpy pillow matplotlib pyqt5
    

Alternatively, use a `requirements.txt` file:

    numpy
    Pillow
    matplotlib
    pyqt5
    

Then run:

    pip install -r requirements.txt
    

* * *

Usage
-----

### Running the Application

To start the application, run the main Python script:

    python PyIMPA.py
    

### User Interface Overview

*   **Left Panel (Display):**
    *   **Loaded Image:**  
        The full-resolution image is shown within a scrollable area so that every pixel is displayed with a 1:1 mapping, ensuring precision.
    *   **Magnifiers:**  
        Two magnifier windows provide zoomed-in views around the selected endpoints.
    *   **Band Preview:**  
        Displays a cross-sectional preview of the intensity “band” extracted perpendicular to the drawn segment.
*   **Right Panel (Controls):**
    *   **Profile Parameters:**  
        Controls for loading images, drawing segments, setting the band extraction width (bandwidth), and calculating intensity profiles.
    *   **Channel Selection:**  
        Choose from “Gray,” “Red,” “Green,” and “Blue” channels.
    *   **Manual Coordinate Edits:**  
        Input fields for precise adjustment of the segment endpoints.
    *   **Visualization Window:**  
        Opens a separate window showing a consolidated view of the image, magnifiers, and band preview.
    *   **Preset Controls:**  
        Save and load presets for analysis and chart styling.
    *   **Chart & Binning Options:**  
        Configure graph titles, axis labels, bin sizes, and styling options for intensity profile plots.

* * *

Software Architecture and Code Structure
----------------------------------------

### Main Components

*   **ImageLabel Class**
    *   **Purpose:** Displays the loaded image at its native resolution and handles user interactions (drawing and dragging segment endpoints).
    *   **Key Methods:**
        *   `load_image()`: Loads an image file, converts it to a NumPy array, extracts the desired channel, and creates a QPixmap.
        *   `update_displayed_pixmap()`: Sets the QLabel’s pixmap to the original image without scaling and calls `adjustSize()` for full-resolution display.
        *   Mouse event handlers (`mousePressEvent()`, `mouseMoveEvent()`, `mouseReleaseEvent()`): Enable drawing and dragging of ROI endpoints.
        *   Coordinate conversion methods: Map between widget coordinates and original image coordinates.
*   **BandPreviewLabel Class**
    *   **Purpose:** Renders a preview of the “band” (rectified cross-section) extracted along the segment.
    *   **Key Method:**
        *   `update_band_image()`: Converts a 2D NumPy array to a QPixmap for display.
*   **MagnifierLabel Class**
    *   **Purpose:** Provides a zoomed-in view around a selected point on the image.
    *   **Key Method:**
        *   `update_magnifier()`: Extracts a cropped region around a point and scales it for detailed inspection.
*   **SeparateWindow Class**
    *   **Purpose:** Opens a separate window that vertically stacks the image display, magnifiers, and band preview for a consolidated view.
*   **SavePresetDialog Class**
    *   **Purpose:** Provides a dialog for saving configuration presets to JSON.
*   **MainWindow Class**
    *   **Purpose:** Integrates all components into one unified interface.
    *   **Layout:**
        *   **Left Panel:** Displays the image (inside a QScrollArea), magnifiers, and band preview.
        *   **Right Panel:** Contains control widgets for image analysis.
    *   **Key Methods:**
        *   `load_image()`, `activate_drawing()`, `apply_manual_coords()`: Manage image loading and ROI definition.
        *   `update_point_info()`: Updates the coordinate display.
        *   `update_band_preview()`, `update_magnifiers()`: Refresh the preview widgets.
        *   `calculate_profile()`, `calculate_multi_channel_profile()`: Compute and plot intensity profiles.
        *   `save_preset()`, `load_preset()`: Handle preset configuration.

* * *

Intensity Profile and Band Extraction Algorithm
-----------------------------------------------

1.  **Segment Definition:**  
    The user defines a segment by selecting two points on the image. Coordinates are mapped directly to the original image (1:1 mapping).
2.  **Intensity Profile Calculation:**
    *   The software interpolates a line between the two selected points.
    *   For each point along the line, the intensity is sampled from the chosen channel.
    *   Binning is applied (if enabled) to compute the mean and standard deviation for each bin.
3.  **Band Extraction:**
    *   For every point along the segment, a perpendicular direction is computed.
    *   A narrow “band” is extracted by sampling across the perpendicular direction.
    *   The band data is transposed and displayed in a preview.
4.  **Multi-Channel Analysis:**  
    The process is repeated for each channel (R, G, B, and Gray), and results are plotted in subplots for comparative analysis.

* * *

Scientific Applications
-----------------------

PyIMPA is designed for quantitative analysis in scientific imaging. Applications include:

*   **Microscopy Imaging:**
    *   Analyze fluorescence intensity or phase contrast profiles in biological specimens.
*   **Materials Science:**
    *   Evaluate the uniformity of coatings, surface textures, and defects in composite materials.
*   **Medical Imaging:**
    *   Extract diagnostic intensity profiles from radiological images.
*   **Optical Spectroscopy:**
    *   Compare spectral intensity distributions across different color channels.

The precise, native-resolution display and accurate coordinate mapping ensure reliable quantitative measurements.

* * *

Customization and Presets
-------------------------

*   **Chart Customization:**  
    Customize graph titles, axis labels, line colors, styles, thickness, and markers for profile plots.
*   **Preset Management:**  
    Save and load presets (stored in JSON) to reproduce analysis configurations across sessions.

* * *

Future Improvements
-------------------

*   **Advanced ROI Selection:**
    *   Support for free-form or multi-segment ROI selection.
*   **Image Processing Integration:**
    *   Additional preprocessing options such as background subtraction or smoothing.
*   **Batch Processing:**
    *   Automate processing of multiple images.
*   **Enhanced Export Options:**
    *   Export profile data and plots in various formats (CSV, PDF, etc.).
*   **UI Enhancements:**
    *   Improved interactive editing of ROI and further customization of the interface.

* * *

License
-------

This software is released under the [MIT License](LICENSE).

* * *

Contributing
------------

Contributions are welcome! Please follow these guidelines:

1.  Fork the repository.
2.  Create a new branch for your feature or bugfix.
3.  Write tests and documentation for your changes.
4.  Submit a pull request with a detailed description of your changes.

For major changes, please open an issue first to discuss the modifications.

* * *

Acknowledgments
---------------

*   Thanks to the developers of PyQt5, NumPy, Matplotlib, and Pillow for their excellent libraries.
*   This project is inspired by the need for precise and reproducible intensity profile measurements in scientific imaging.

* * *

_For further information, please refer to the source code or contact the maintainers._
