Alex-MP-20 Screening Dataset
============================

This directory contains candidate structures derived from the Alex-MP-20 dataset
during the screening process for fluoride-ion battery (FIB) materials.

The subdirectories correspond to different stages of the screening workflow.
The color labels are consistent with those used in the screening workflow figure.


Directory Description
---------------------

RED
    Initial fluoride-containing structures selected from the Alex-MP-20 dataset.

ORANGE
    Structures selected after thermodynamic stability screening using MatterSim.
    Screening criteria include:
    - Energy above convex hull <= 0.1 eV/atom
    - SUN (Stable, Unique, and Novel) screening

YELLOW
    Structures satisfying the ALIGNN-predicted band-gap criterion:
    - Band gap > 3.5 eV

GREEN
    Structures remaining after elemental filtering.
    Structures containing noble gases, radioactive elements, or Hg were excluded.

BLUE
    Structures remaining after oxidation-state screening.

NAVY
    Structures selected for subsequent DFT validation.


Number of Structures
--------------------

RED       : 2,356 structures
ORANGE    : 2,356 structures
YELLOW    : 672 structures
GREEN     : 670 structures
BLUE      : 438 structures
NAVY      : 404 structures


File Format
-----------

Each candidate is stored in an individual subdirectory.
Crystal structures are provided in VASP POSCAR format.


Notes
-----

The structures in this directory represent intermediate screening stages.
Final candidate structures obtained after DFT-based screening are provided
separately in the ../structures/ directory.
