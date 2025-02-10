
# Python Intensity Multi-channel Profile Analyzer (PyIMPA)

**Python Intensity Multi-channel Profile Analyzer (PyIMPA)** is a scientific imaging tool written in Python that enables researchers to perform precise intensity profile analysis on both RGB and grayscale images. With an intuitive graphical user interface (GUI) built with PyQt5, PyIM allows users to load images, define regions of interest (ROI) by drawing line segments, extract intensity profiles, and visualize detailed cross-sectional (“band”) information. The software supports multi-channel analysis, customizable chart styling, and preset saving/loading, making it ideal for applications in microscopy, medical imaging, materials science, and other research fields requiring quantitative image analysis.

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

    python pyim.py
    

### User Interface Overview

*   **Left Panel (Display):**
    *   **Loaded Image:** The full-resolution image is shown within a scrollable area so that every pixel is displayed with a 1:1 mapping, ensuring precision.
    *   **Magnifiers:** Two magnifier windows provide zoomed-in views around the selected endpoints.
    *   **Band Preview:** Displays a cross-sectional preview of the intensity “band” extracted perpendicular to the drawn segment.
*   **Right Panel (Controls):**
    *   **Profile Parameters:** Controls for loading images, drawing segments, setting the band extraction width (bandwidth), and calculating intensity profiles.
    *   **Channel Selection:** Choose from “Gray,” “Red,” “Green,” and “Blue” channels.
    *   **Manual Coordinate Edits:** Input fields for precise adjustment of the segment endpoints.
    *   **Visualization Window:** Opens a separate window showing a consolidated view of the image, magnifiers, and band preview.
