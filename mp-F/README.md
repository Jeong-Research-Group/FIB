MP-F Screening Dataset

This directory contains candidate structures derived from the Alex-MP-20 dataset
during the screening process for fluoride-ion battery (FIB) materials.

The subdirectories correspond to different stages of the screening workflow.
The color labels are consistent with those used in the screening workflow figure.

Directory Description

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
Structures selected for subsequent DFT validation using VASP.

Number of Structures

RED       :  21,600 structures
ORANGE    :  13,235 structures
YELLOW    :    1259 structures
GREEN     :    1227 structures
BLUE      :     877 structures
NAVY      :     801 structures

File Format

Each candidate is stored in an individual subdirectory.
Crystal structures are provided in VASP POSCAR and CIF (.cif) formats.

Computational Tools

The screening workflow employs the following computational tools and datasets:

* Alex-MP-20
    Source dataset for the initial materials screening.
* MatterSim
    Used for machine-learning-based structural and thermodynamic stability
    evaluation.
* ALIGNN (Atomistic Line Graph Neural Network)
    Used for machine-learning-based prediction of electronic band gaps.
* VASP (Vienna Ab initio Simulation Package)
    Used for density functional theory (DFT) validation of the screened
    candidate structures.

Notes

The structures in this directory represent intermediate screening stages.

The screening procedure progressively reduces the initial fluoride-containing
materials to candidates satisfying thermodynamic stability, electronic,
elemental, and oxidation-state criteria.

Final candidate structures obtained after DFT-based screening are provided
separately in the ../structures/ directory.

References

[1] Alex-MP-20 / MatterGen

C. Zeni, R. Pinsler, D. Zügner, A. Fowler, M. Horton, X. Fu, Z. Wang,
A. Shysheya, J. Crabbé, S. Ueda, R. Sordillo, L. Sun, J. Smith,
B. Nguyen, H. Schulz, S. Lewis, C.-W. Huang, Z. Lu, Y. Zhou, H. Yang,
H. Hao, J. Li, C. Yang, W. Li, and R. Tomioka,
"A generative model for inorganic materials design,"
Nature (2025).
DOI: 10.1038/s41586-025-08628-5

[2] MatterSim

H. Yang, C. Hu, Y. Zhou, X. Liu, Y. Shi, J. Li, G. Li, Z. Chen,
S. Chen, C. Zeni, M. Horton, R. Pinsler, A. Fowler, D. Zügner,
T. Xie, J. Smith, L. Sun, Q. Wang, L. Kong, C. Liu, H. Hao,
and Z. Lu,
"MatterSim: A Deep Learning Atomistic Model Across Elements,
Temperatures and Pressures,"
arXiv:2405.04967 (2024).
DOI: 10.48550/arXiv.2405.04967

[3] ALIGNN

K. Choudhary and B. DeCost,
"Atomistic Line Graph Neural Network for improved materials
property predictions,"
npj Computational Materials, 7, 185 (2021).
DOI: 10.1038/s41524-021-00650-1

[4] VASP

G. Kresse and J. Furthmüller,
"Efficient iterative schemes for ab initio total-energy calculations
using a plane-wave basis set,"
Physical Review B, 54, 11169-11186 (1996).
DOI: 10.1103/PhysRevB.54.11169

[5] VASP

G. Kresse and J. Furthmüller,
"Efficiency of ab-initio total energy calculations for metals and
semiconductors using a plane-wave basis set,"
Computational Materials Science, 6, 15-50 (1996).
DOI: 10.1016/0927-0256(96)00008-0

[6] PAW Method / VASP

G. Kresse and D. Joubert,
"From ultrasoft pseudopotentials to the projector augmented-wave method,"
Physical Review B, 59, 1758-1775 (1999).
DOI: 10.1103/PhysRevB.59.1758
