# Python Multi-channel Intensity Profile Analyser (PyMIPA)

**Python Multi-channel Intensity Profile Analyser (PyMIPA)** is a scientific imaging tool written in Python that enables researchers to perform precise intensity profile analysis on both RGB and grayscale images. With an intuitive graphical user interface (GUI) built with PyQt5, PyMIPA allows users to load images, define regions of interest (ROI) by drawing line segments, extract intensity profiles, and visualize detailed cross-sectional (“band”) information. The software supports multi-channel analysis, customizable chart styling, and preset saving/loading, making it ideal for applications in microscopy, medical imaging, materials science, and other research fields requiring quantitative image analysis.

---

## Table of Contents

- [Features](##features)
- [Installation](##installation)
- [Usage](##usage)
- [Software Architecture and Code Structure](#software-architecture-and-code-structure)
- [Intensity Profile and Band Extraction Algorithm](#intensity-profile-and-band-extraction-algorithm)
- [Scientific Applications](#scientific-applications)
- [Customization and Presets](#customization-and-presets)
- [Future Improvements](#future-improvements)
- [License](#license)
- [Contributing](#contributing)
- [Acknowledgments](#acknowledgments)

---

## Features

- **Image Loading and Display**
  - Supports common image formats (PNG, JPEG, BMP, TIFF, etc.)
  - Displays images at their native resolution in a scrollable view for precise analysis.

- **Multi-Channel Support**
  - Works with both RGB and grayscale images.
  - Enables extraction of individual channels (Red, Green, Blue) or a computed grayscale (average).

- **ROI and Segment Definition**
  - Draw segments directly on the image by selecting two points.
  - Supports manual coordinate entry for precise segment placement.
  - Visual feedback with overlaid handles and lines drawn on the image.

- **Band Extraction and Preview**
  - Extracts a rectified “band” (cross-sectional profile) perpendicular to the drawn segment.
  - Displays a band preview showing the extracted cross-section of intensity values.

- **Intensity Profile Calculation**
  - Computes mean intensity values along the defined segment.
  - Supports binning of intensity values and plots standard deviation (error bars) for quantitative analysis.
  - Provides multi-channel profile plots to compare channel-specific intensity distributions.

- **Visualization Tools**
  - Two magnifier windows provide zoomed-in views around the selected endpoints.
  - A separate visualization window can be opened for a consolidated view of the image, magnifiers, and band preview.

- **Preset Saving and Loading**
  - Save analysis and chart styling options to a JSON file.
  - Load saved presets to quickly reapply previous configurations.

---

## Installation

### Prerequisites

- **Python 3.6+**
- **pip**

### Dependencies

Install the required Python packages using pip:

```bash
pip install numpy pillow matplotlib pyqt5
