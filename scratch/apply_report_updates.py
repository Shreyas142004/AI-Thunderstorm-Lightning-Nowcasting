import re
from pathlib import Path

# Load papers data from build_chapter2.py
from build_chapter2 import papers_data

print(f"Loaded {len(papers_data)} papers.")

# 1. Generate new thebibliography block
bib_entries = []
for p in papers_data:
    entry = f"""\\bibitem{{{p['key']}}}
{p['authors']}, ``{p['title']},'' \\emph{{{p['journal']}}}, {p['volume']}, {p['year']}, doi: {p['doi']}."""
    bib_entries.append(entry)

new_bibliography = "\\begin{thebibliography}{99}\n\n" + "\n\n".join(bib_entries) + "\n\n\\end{thebibliography}"

# 2. Generate Section 2.1 Existing Studies (3 paragraphs, citing in numerical order [1] to [25])
new_existing_studies = r"""\section{Existing Studies}
Recent investigations in convective nowcasting and severe storm modeling have achieved significant breakthroughs through specialized loss formulations, deep physical soundings, and machine learning ensembles. Addressing the extreme spatial imbalance between quiescent background regions and active storm cores, Tian et al. \cite{tian2026dual} formulated dual-weighted loss functions that penalize missed detections in high-reflectivity convective centers. Incorporating non-linear functional representations, Chen et al. \cite{chen2026clka} coupled convolutional recurrent networks with Kolmogorov-Arnold Networks (KAN) to map physical sounding profiles to total lightning flash rates. Operational ensemble evaluations across northern India by Kumar et al. \cite{kumar2026enhancing} demonstrated that Gradient Boosted Decision Tree (GBDT) architectures (XGBoost and LightGBM) consistently outperform deep neural networks on tabular sounding datasets. Remote sensing pre-convective indicators were advanced by Wang et al. \cite{wang2026infrared}, who demonstrated that rapid brightness temperature drops in geostationary split-window infrared channels signal cloud-top glaciation and imminent lightning. To prioritize developing convective cores over dissipating anvil debris, Li et al. \cite{li2026nowcasting} integrated spatial attention mechanisms into Conv-GRU backbones for cloud-to-ground flash density mapping. Establishing direct physical reflectivity warning thresholds, Li et al. \cite{li2026correlation} verified that $40$~dBZ radar echo volumes extending above the freezing level provide unambiguous operational precursors of surface lightning discharges.

Multimodal data fusion and remote sensing validation have significantly expanded operational observation coverage across diverse geographical domains. Deploying self-supervised representation learning, Zhang et al. \cite{zhang2025lightning} fused optical satellite imagery with high-frequency lightning telemetry to track convective storm translation. Ground-based remote sensing validation across the Indian subcontinent by Ghosh et al. \cite{ghosh2025assessment} established that the Indian Lightning Location Network (ILLN) achieves detection efficiencies exceeding 88\%, while highlighting pronounced terrain-induced signal attenuation across the Western Ghats. In satellite meteorology, Sharma et al. \cite{sharma2025insat} leveraged Indian INSAT-3D thermal infrared channels to identify pre-convective cloud clusters before surface precipitation begins. Focusing on southern India, Rayudu et al. \cite{rayudu2025prediction} evaluated deep recurrent architectures (ConvLSTM and PredRNN) on Doppler Weather Radar (DWR) reflectivity grids to model localized cell translation and decay. To address severe autocorrelation in weather time series, Le and Vargas \cite{le2024autocorrelated} developed conditioned Latin hypercube sampling methods for spatiotemporal predictive datasets. Polarimetric radar capabilities were explored by Rombeek et al. \cite{rombeek2024exploiting}, who proved that dual-polarization radar parameters ($Z_{DR}, K_{DP}$) substantially enhance deep learning hydrometeor classification during thunderstorm intensification. Demonstrating the vital necessity of boundary-layer surface physics, Kim et al. \cite{kim2024improvements} established that fusing automated weather station (AWS) surface factors---specifically dry-bulb temperature, relative humidity, and pressure---with radar rain rate significantly slows nowcast degradation beyond 30 minutes. In operational US meteorology, Cintineo et al. \cite{cintineo2024probsevere} established NOAA's ProbSevere v3 framework, demonstrating that multi-sensor GBDT data fusion combining radar, satellite, and numerical model fields provides superior calibrated severe storm probabilities.

Foundational investigations have systematically elucidated the physical dependencies, tracking algorithms, and tree-based ensemble methods governing convective weather nowcasting. Analyzing seasonal lightning dynamics across Indian climate zones, Soni et al. \cite{soni2023machine} demonstrated the strong geographic dependency of electrical discharges on Convective Available Potential Energy (CAPE) and total precipitable water. Enhancing feature diversity, Song et al. \cite{song2023lightning} achieved 94.3\% classification accuracy by pairing aerosol concentrations with satellite data in LightGBM ensembles. To prevent spatial blurring across long horizons, Lu et al. \cite{lu2023mcgln} deployed multimodal ConvLSTM generative adversarial networks (GANs) on radar and lightning streams. Operational numerical weather prediction improvements were demonstrated by Das et al. \cite{das2023impact}, who verified that 3D-Var assimilation of Doppler radar reflectivity and lightning data into numerical models substantially reduces short-range precipitation forecast displacement errors. For complex mountainous terrain, Leinonen et al. \cite{leinonen2023multihazard} implemented deep multi-hazard data fusion architectures. Specifically within Karnataka, Toropova et al. \cite{toropova2022characteristics} conducted an extensive empirical radar investigation over Gadag ($15^\circ\text{N}$), analyzing more than 2,500 convective clouds and 5,000 electrical discharges to prove that maximum radar reflectivity ($Z_{\max}$), cloud-top height, and lightning frequency surge during post-monsoon transition periods. To capture non-rigid convective motion over complex terrain, Leinonen et al. \cite{leinonen2022seamless} formulated seamless 60-minute recurrent-convolutional nowcasts. Spatiotemporal event tracking was further refined by Sibolla et al. \cite{sibolla2021determining} through graph-theoretic clustering algorithms mapping real-time strike trajectories. In a comprehensive predictor analysis, Leinonen et al. \cite{leinonen2021nowcasting} evaluated 106 atmospheric predictors to confirm that surface moisture soundings and radar data represent the dominant drivers of next-hour storm hazards. Addressing non-linear cloud advection, Luo et al. \cite{luo2021pfst} introduced pseudoflow spatiotemporal LSTM cells for radar extrapolation. Earlier satellite nowcasting in India was established by Goyal et al. \cite{goyal2017satellite}, who utilized INSAT-3D thermal infrared imagery with ForTraCC tracking for short-range thunderstorm warnings. While these twenty-five studies advance radar tracking, deep learning, and tree ensembles, they either operate at coarse synoptic scales or lack localized thermodynamic grounding and accessible decision-support interfaces for rural tropical regions."""

# 3. Generate Comparative Table (All 25 papers in exact order 1 to 25 + Proposed System)
table_rows = []
for p in papers_data:
    row = f"``{p['title']}'' \\cite{{{p['key']}}} & {p['year']} & {p['desc']} & \\textbf{{Pro:}} {p['pros']} \\newline \\textbf{{Con:}} {p['cons']} \\\\ \\hline"
    table_rows.append(row)

# Proposed system row
proposed_row = r"""\rowcolor{gray!10}
\textbf{Proposed System (AeroCast AI)} & \textbf{2026} & \textbf{Unified 27-yr Karnataka climatology, 62-feat GBDT ensemble, and Gemini LLM synoptic bulletins.} & \textbf{Pro:} 0--90m nowcast, zero nocturnal false alarms, interactive radar UI. \newline \textbf{Con:} Bounded to Karnataka boundary; multi-state in Ph-II. \\ \hline"""
table_rows.append(proposed_row)

new_comparative_table = r"""\section{Comparative Summary}
A detailed comparative analysis of all twenty-five surveyed research papers against the proposed nowcasting architecture is presented in Table~\ref{tab:lit_comparison}. The comparison underscores the novelty of the proposed framework in unifying a 27-year regional climatological dataset, continuous thermodynamic boundary-layer indices, gradient boosted tree ensembles, and LLM-driven generative meteorological bulletins within a single localized web platform.

\begingroup
\hyphenpenalty=50
\exhyphenpenalty=50
\sloppy
\begin{xltabular}{\textwidth}{|L{4.2cm}|C{1.1cm}|L{4.2cm}|Y|}
\caption{Comparative Summary of Surveyed Research Papers}\label{tab:lit_comparison} \\
\hline
\hdrrow \textbf{Paper Title} & \textbf{Year} & \textbf{Description} & \textbf{Pros \& Cons} \\ \hline
\endfirsthead
\hline
\hdrrow \textbf{Paper Title} & \textbf{Year} & \textbf{Description} & \textbf{Pros \& Cons} \\ \hline
\endhead
\hline
\endfoot
\hline
\endlastfoot

""" + "\n".join(table_rows) + "\n\\end{xltabular}\n\\endgroup"

print("Generated Section 2.1, Comparative Table (25 papers), and Bibliography!")

with open('scratch/generated_chapter2.tex', 'w', encoding='utf-8') as f:
    f.write(new_existing_studies + "\n\n" + new_comparative_table + "\n\n" + new_bibliography)

print("Saved scratch/generated_chapter2.tex")
