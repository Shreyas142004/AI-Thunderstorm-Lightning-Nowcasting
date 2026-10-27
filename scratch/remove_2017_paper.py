with open('report/AeroCast_AI_Report.tex', 'r', encoding='utf-8') as f:
    text = f.read()

# 1. In Section 2.1: remove Goyal et al. sentence and change twenty-five to twenty-four
target_p3_old = r'''Addressing non-linear cloud advection, Luo et al. \cite{luo2021pfst} introduced pseudoflow spatiotemporal LSTM cells for radar extrapolation. Earlier satellite nowcasting in India was established by Goyal et al. \cite{goyal2017satellite}, who utilized INSAT-3D thermal infrared imagery with ForTraCC tracking for short-range thunderstorm warnings. While these twenty-five studies advance radar tracking, deep learning, and tree ensembles, they either operate at coarse synoptic scales or lack localized thermodynamic grounding and accessible decision-support interfaces for rural tropical regions.'''

target_p3_new = r'''Addressing non-linear cloud advection, Luo et al. \cite{luo2021pfst} introduced pseudoflow spatiotemporal LSTM cells for radar extrapolation. While these twenty-four studies advance radar tracking, deep learning, and tree ensembles, they either operate at coarse synoptic scales or lack localized thermodynamic grounding and accessible decision-support interfaces for rural tropical regions.'''

assert target_p3_old in text, "target_p3_old not found!"
text = text.replace(target_p3_old, target_p3_new)

# 2. In Section 2.2: change twenty-five to twenty-four
target_comp_old = r'''A detailed comparative analysis of all twenty-five surveyed research papers against the proposed nowcasting architecture is presented in Table~\ref{tab:lit_comparison}.'''
target_comp_new = r'''A detailed comparative analysis of all twenty-four surveyed research papers against the proposed nowcasting architecture is presented in Table~\ref{tab:lit_comparison}.'''

assert target_comp_old in text, "target_comp_old not found!"
text = text.replace(target_comp_old, target_comp_new)

# 3. In Table 2.1: remove Goyal row
target_row = r'''``Satellite-Based Technique for Nowcasting of Thunderstorms Over Indian Region'' \cite{goyal2017satellite} & 2017 & Operational thunderstorm tracking using INSAT-3D thermal infrared imagery and ForTraCC tracking over India. & \textbf{Pro:} Pioneered automated satellite cloud cluster tracking for thunderstorm warnings across India. \newline \textbf{Con:} High false alarm rate due to absence of boundary-layer thermodynamic soundings and ML classification. \\ \hline
'''
assert target_row in text, "target_row not found!"
text = text.replace(target_row, '')

# 4. In thebibliography: remove Goyal bibitem
target_bib = r'''\bibitem{goyal2017satellite}
S.~Goyal, A.~Kumar, M.~Mohapatra, L.~S. Rathore, S.~K. Dube, R.~Saxena, and R.~K. Giri, ``Satellite-Based Technique for Nowcasting of Thunderstorms Over Indian Region,'' \emph{Journal of Earth System Science}, vol. 126, art. no. 79, 2017, doi: 10.1007/s12040-017-0859-2.
'''
assert target_bib in text, "target_bib not found!"
text = text.replace(target_bib, '')

with open('report/AeroCast_AI_Report.tex', 'w', encoding='utf-8') as f:
    f.write(text)

print("Successfully removed the 2017 research paper (Goyal et al.) and updated counts to 24!")
