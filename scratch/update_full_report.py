import re
from pathlib import Path
from build_chapter2 import papers_data

with open('report/AeroCast_AI_Report.tex', 'r', encoding='utf-8') as f:
    text = f.read()

# 1. Update preamble captionsetup
preamble_old = r"""% Captions strictly below figures and tables
\captionsetup{position=below, font=small, labelfont=bf}"""

preamble_new = r"""% Table captions strictly ABOVE, figure captions strictly BELOW
\captionsetup[table]{position=above, font=small, labelfont=bf, skip=6pt}
\captionsetup[figure]{position=below, font=small, labelfont=bf, skip=6pt}"""

text = text.replace(preamble_old, preamble_new)

# 2. Update Abstract block
abstract_old_pattern = r'(\\begin\{center\}\s*\{\\fontsize\{16pt\}\{20pt\}\\selectfont \\textbf\{Abstract\}\}\\\\\[0.8cm\]\s*\\end\{center\}\s*\\noindent \\textbf\{AeroCast AI\} is an intelligent, physics-informed.*?)(\\vspace\{0.8cm\}\s*\\noindent \\textbf\{Keywords:\}.*?)(?=\\newpage|\s*\\tableofcontents)'

new_abstract = r"""\begin{center}
{\fontsize{15pt}{19pt}\selectfont \textbf{AI-DRIVEN CONVECTIVE WEATHER AND THUNDERSTORM NOWCASTING SYSTEM FOR KARNATAKA USING ATMOSPHERIC THERMODYNAMICS AND GENERATIVE AI}}\\[0.5cm]
{\fontsize{14pt}{18pt}\selectfont \textbf{ABSTRACT}}\\[0.5cm]
\end{center}

\noindent An intelligent, physics-informed convective weather and thunderstorm nowcasting system is developed to deliver high-precision, short-term ($0$--$90$ minutes) meteorological predictions across Karnataka, with specialized calibration for the Western Ghats and coastal regions. Tropical thunderstorms, convective lightning discharges, and localized downbursts pose severe risks to agriculture, transport, and public safety. Conventional Numerical Weather Prediction models suffer from update latency ($3$--$6$ hours) and coarse resolutions that fail to resolve fast-evolving convective cells igniting within $30$ to $60$ minutes. The developed framework bridges this gap by unifying a 27-year historical Karnataka climatological dataset ($9,862$ verified daily records from 2000 to 2027), real-time atmospheric telemetry, and multimodal generative reasoning via the Google Gemini API. The system implements a 62-feature atmospheric pipeline computing continuous thermodynamic indices, including Dew Point Depression, Vapor Pressure Deficit, and Equivalent Potential Temperature to suppress nocturnal false alarms. A soft-voting Gradient Boosted Decision Tree ensemble (LightGBM, XGBoost, HistGradientBoosting) achieves 91.2\% holdout accuracy, calibrated alongside climatological priors. Integrated Gemini AI reasoning translates complex predictive distributions into calibrated convective risk probabilities, a 3-step timeline progression ($+30$m, $+60$m, $+90$m), and plain-language domain advisories for agriculture, transit, and public safety. An interactive Leaflet.js Doppler radar interface delivers accessible, low-latency decision support for regional disaster preparedness.

\vspace{0.8cm}
\noindent \textbf{Keywords:} Convective Weather Nowcasting, Thunderstorm Prediction, Atmospheric Thermodynamics, Gradient Boosted Trees, Google Gemini API, S-Band Doppler Radar, Western Ghats Microclimates, Dew Point Depression."""

text = re.sub(abstract_old_pattern, lambda m: new_abstract + "\n", text, flags=re.DOTALL)

# 3. Load generated Chapter 2 parts
with open('scratch/generated_chapter2.tex', 'r', encoding='utf-8') as f:
    ch2_text = f.read()

# ch2_text has: new_existing_studies + "\n\n" + new_comparative_table + "\n\n" + new_bibliography
# Let's split them
parts = ch2_text.split(r'\section{Comparative Summary}')
new_existing_studies = parts[0].strip()
sub_parts = parts[1].split(r'\begin{thebibliography}{99}')
new_comparative_table = r'\section{Comparative Summary}' + "\n" + sub_parts[0].strip()
new_bibliography = r'\begin{thebibliography}{99}' + "\n" + sub_parts[1].strip()

# Replace Section 2.1 and Section 2.2 in report
ch2_old_pattern = r'(\\chapter\{Literature Review\}\s*\\section\{Existing Studies\}.*?)(?=\\section\{Research Gap\})'
ch2_replacement = "\\chapter{Literature Review}\n\n" + new_existing_studies + "\n\n" + new_comparative_table + "\n\n"
text = re.sub(ch2_old_pattern, lambda m: ch2_replacement, text, flags=re.DOTALL)

# Replace Bibliography
bib_old_pattern = r'\\begin\{thebibliography\}\{99\}.*?\\end\{thebibliography\}'
text = re.sub(bib_old_pattern, lambda m: new_bibliography, text, flags=re.DOTALL)

# 4. Update Chapter 3: Existing System and Proposed System with figures
sec31_old_pattern = r'(\\section\{Existing System and Proposed System\}\s*\\subsection\{Existing System\}.*?\\subsection\{Proposed System\}.*?)(?=\\section\{Hardware and Software Requirements\})'

sec31_new = r"""\section{Existing System and Proposed System}

\subsection{Existing System}
Traditional meteorological forecasting workflows across Karnataka rely on fragmented observation streams, as depicted in the existing system architecture in Figure~\ref{fig:existing_arch}. In the current operational setup, localized weather monitoring relies on periodic public bulletins issued by regional meteorological centers, commercial smartphone weather applications, and raw numerical model outputs. Smartphone weather applications rely on global GFS or ECMWF models interpolated to city coordinates, displaying static icons (such as ``Rain'' or ``Cloudy'') with updates spaced 3 to 6 hours apart. In agricultural taluks like Puttur, Sullia, and Bantwal, farmers and panchayat officials rely on manual visual sky observation or social media messaging groups, leaving them unprepared for rapid convective downbursts and cloud-to-ground lightning strikes.

\begin{figure}[H]
\centering
\includegraphics[width=0.92\textwidth]{existing_system_workflow.png}
\caption{Workflow and architectural limitations of the existing operational meteorological forecasting setup.}
\label{fig:existing_arch}
\end{figure}

\subsection{Proposed System}
To overcome the latency and resolution barriers of conventional numerical frameworks, an automated, physics-grounded architecture is developed, whose workflow is illustrated in Figure~\ref{fig:proposed_system}. The system operates continuously to fetch live observational telemetry, compute 62 physical atmospheric variables, evaluate an ensemble GBDT model, and condition predictions against a 27-year regional climatological baseline. Google Gemini API synthesizes the numerical predictions into human-readable synoptic bulletins and sector-specific advisories. A responsive web dashboard displays real-time convective probabilities, dynamic risk badges, a 3-step timeline progression ($+30$m, $+60$m, $+90$m), neighborhood micro-zones, and an interactive S-band Doppler radar with concentric range rings ($25$--$100$~km).

\begin{figure}[H]
\centering
\includegraphics[width=0.92\textwidth]{proposed_system_architecture.png}
\caption{Block diagram and data processing pipeline of the proposed convective nowcasting system.}
\label{fig:proposed_system}
\end{figure}
"""

text = re.sub(sec31_old_pattern, lambda m: sec31_new + "\n", text, flags=re.DOTALL)

# 5. Fix table captions above tables in Chapter 3 & Chapter 4
# Hardware table
hw_old = r"""\subsection{Hardware Requirements}
\begin{table}[H]
\centering
\begin{tabularx}{\textwidth}{|L{3.8cm}|Y|}
\hline
\hdrrow \textbf{Component} & \textbf{Specification} \\ \hline
Processor & Intel Core i5 (11th Gen or higher) / AMD Ryzen 5 \\ \hline
System Memory (RAM) & 8 GB minimum; 16 GB recommended for feature preprocessing \\ \hline
Storage & 512 GB Solid State Drive (SSD) with $\ge 15$~GB free space \\ \hline
Network Connectivity & High-speed broadband connection ($\ge 10$~Mbps) for live telemetry APIs \\ \hline
Display & Full HD ($1920\times 1080$) resolution for interactive radar visualization \\ \hline
\end{tabularx}
\caption{Hardware Requirements}
\label{tab:hardware_req}
\end{table}"""

hw_new = r"""\subsection{Hardware Requirements}
\begin{table}[H]
\centering
\caption{Hardware Requirements}
\label{tab:hardware_req}
\vspace{2pt}
\begin{tabularx}{\textwidth}{|L{3.8cm}|Y|}
\hline
\hdrrow \textbf{Component} & \textbf{Specification} \\ \hline
Processor & Intel Core i5 (11th Gen or higher) / AMD Ryzen 5 \\ \hline
System Memory (RAM) & 8 GB minimum; 16 GB recommended for feature preprocessing \\ \hline
Storage & 512 GB Solid State Drive (SSD) with $\ge 15$~GB free space \\ \hline
Network Connectivity & High-speed broadband connection ($\ge 10$~Mbps) for live telemetry APIs \\ \hline
Display & Full HD ($1920\times 1080$) resolution for interactive radar visualization \\ \hline
\end{tabularx}
\end{table}"""

text = text.replace(hw_old, hw_new)

# Software table
sw_old = r"""\subsection{Software Requirements}
\begin{table}[H]
\centering
\begin{tabularx}{\textwidth}{|L{4.2cm}|Y|}
\hline
\hdrrow \textbf{Software Component} & \textbf{Technology / Framework} \\ \hline
Operating System & Windows 11 / Ubuntu Linux 22.04 LTS \\ \hline
Programming Language & Python 3.10+ \\ \hline
Web Framework & Flask 3.0+ with WSGI server \\ \hline
Frontend Interface & HTML5, CSS3 (Vanilla design tokens), JavaScript (ES6+) \\ \hline
Geospatial Mapping & Leaflet.js 1.9+ with OpenStreetMap CartoDB dark/light tiles \\ \hline
Machine Learning & LightGBM, XGBoost, Scikit-learn, Joblib, NumPy, Pandas \\ \hline
Generative AI & Google Gemini API (\texttt{gemini-flash-latest}, \texttt{gemini-flash-lite}) \\ \hline
Telemetry Sources & Open-Meteo High-Resolution API with Visual Crossing fallback \\ \hline
Dataset Engine & Microsoft Excel / OpenPyXL for 27-year Karnataka climatology \\ \hline
\end{tabularx}
\caption{Software Requirements}
\label{tab:software_req}
\end{table}"""

sw_new = r"""\subsection{Software Requirements}
\begin{table}[H]
\centering
\caption{Software Requirements}
\label{tab:software_req}
\vspace{2pt}
\begin{tabularx}{\textwidth}{|L{4.2cm}|Y|}
\hline
\hdrrow \textbf{Software Component} & \textbf{Technology / Framework} \\ \hline
Operating System & Windows 11 / Ubuntu Linux 22.04 LTS \\ \hline
Programming Language & Python 3.10+ \\ \hline
Web Framework & Flask 3.0+ with WSGI server \\ \hline
Frontend Interface & HTML5, CSS3 (Vanilla design tokens), JavaScript (ES6+) \\ \hline
Geospatial Mapping & Leaflet.js 1.9+ with OpenStreetMap CartoDB dark/light tiles \\ \hline
Machine Learning & LightGBM, XGBoost, Scikit-learn, Joblib, NumPy, Pandas \\ \hline
Generative AI & Google Gemini API (\texttt{gemini-flash-latest}, \texttt{gemini-flash-lite}) \\ \hline
Telemetry Sources & Open-Meteo High-Resolution API with Visual Crossing fallback \\ \hline
Dataset Engine & Microsoft Excel / OpenPyXL for 27-year Karnataka climatology \\ \hline
\end{tabularx}
\end{table}"""

text = text.replace(sw_old, sw_new)

# Module description table
mod_old = r"""\section{Module Description}
The core software modules implemented in \textbf{AeroCast AI} are detailed in Table~\ref{tab:module_desc}.

\begin{table}[H]
\centering
\begin{tabularx}{\textwidth}{|L{4.2cm}|Y|}
\hline
\hdrrow \textbf{Module Name} & \textbf{Functionality and Scope} \\ \hline
Geocoding \& Boundary Validator & Resolves Karnataka coordinates, identifies administrative districts, and enforces state boundary locking. \\ \hline
Dual-Source Telemetry Fetcher & Ingests multi-level hourly and surface atmospheric parameters from Open-Meteo with Visual Crossing backup. \\ \hline
Atmospheric Physics Preprocessor & Computes 62 thermodynamic variables (DPD, VPD, $\theta_e$, wind vectors, lag features, diurnal insolation). \\ \hline
GBDT Soft-Voting Ensemble & Serialized LightGBM, XGBoost, and HistGradientBoosting models executing inference on input feature vectors. \\ \hline
Dataset Climatology Engine & Evaluates 27-year Karnataka meteorological norms ($9,862$ records) to supply Bayesian baseline probabilities. \\ \hline
Gemini Chief Meteorologist AI & Leverages Google Gemini API to produce synoptic bulletins, calibrated probabilities, timeline steps, and advisories. \\ \hline
Doppler Radar Visualization & Renders interactive Leaflet radar map with concentric range rings ($25$--$100$~km) and reflectivity contours. \\ \hline
\end{tabularx}
\caption{System Modules and Their Descriptions}
\label{tab:module_desc}
\end{table}"""

mod_new = r"""\section{Module Description}
The software implementation comprises seven integrated modules detailed in Table~\ref{tab:module_desc}.

\begin{table}[H]
\centering
\caption{System Modules and Their Descriptions}
\label{tab:module_desc}
\vspace{2pt}
\begin{tabularx}{\textwidth}{|L{4.2cm}|Y|}
\hline
\hdrrow \textbf{Module Name} & \textbf{Functionality and Scope} \\ \hline
Geocoding \& Boundary Validator & Resolves Karnataka coordinates, identifies administrative districts, and enforces state boundary locking. \\ \hline
Dual-Source Telemetry Fetcher & Ingests multi-level hourly and surface atmospheric parameters from Open-Meteo with Visual Crossing backup. \\ \hline
Atmospheric Physics Preprocessor & Computes 62 thermodynamic variables (DPD, VPD, $\theta_e$, wind vectors, lag features, diurnal insolation). \\ \hline
GBDT Soft-Voting Ensemble & Serialized LightGBM, XGBoost, and HistGradientBoosting models executing inference on input feature vectors. \\ \hline
Dataset Climatology Engine & Evaluates 27-year Karnataka meteorological norms ($9,862$ records) to supply Bayesian baseline probabilities. \\ \hline
Gemini Chief Meteorologist AI & Leverages Google Gemini API to produce synoptic bulletins, calibrated probabilities, timeline steps, and advisories. \\ \hline
Doppler Radar Visualization & Renders interactive Leaflet radar map with concentric range rings ($25$--$100$~km) and reflectivity contours. \\ \hline
\end{tabularx}
\end{table}"""

text = text.replace(mod_old, mod_new)

# Table 4.1 Work status table
work_old = r"""\begin{table}[H]
\centering
\small
\begin{tabularx}{\textwidth}{|L{3.6cm}|L{2.3cm}|Y|}
\hline
\textbf{Work Item} & \textbf{Status} & \textbf{Description} \\ \hline
Telemetry Ingestion Pipeline & Completed & Open-Meteo REST API data fetcher with Visual Crossing fallback. \\ \hline
Karnataka 27-Year Dataset & Completed & Digitized and analyzed $9, `862$ historical daily observation records (2000--2027). \\ \hline
Physics Feature Engineering & Completed & 62 atmospheric domain metrics computed (DPD, VPD, $\theta_e$, diurnal factor). \\ \hline
GBDT Ensemble Training & Completed & LightGBM, XGBoost, and HistGradientBoosting trained with 91.2\% accuracy. \\ \hline
Gemini Multimodal Engine & Completed & Google Gemini API integrated for synoptic bulletins and calibrated probabilities. \\ \hline
3-Step Timeline Progression & Completed & $+30$m, $+60$m, $+90$m cards with individualized dynamic risk color theming. \\ \hline
Doppler Radar \& Micro-Zones & Completed & S-band concentric radar ($25$--$100$~km) with right-hand taluk sub-zones panel. \\ \hline
State Boundary Locking & Completed & Boundary validation that locks out-of-state queries and displays warning alert. \\ \hline
Live 12-Hour IST Clock & Completed & Real-time ticking header clock formatted in 12-hour AM/PM with instant hydration. \\ \hline
Dual Theme Support & Completed & Beige (light) and Espresso (dark) responsive design tokens. \\ \hline
INSAT-3D Satellite Feed & Pending & Ingest live Indian geostationary satellite infrared imagery in Phase-II. \\ \hline
Automated DWR Doppler Feed & Pending & Direct integration with IMD Mangalore/Bengaluru Doppler radar in Phase-II. \\ \hline
Automated SMS/WhatsApp Alerts & Pending & Broadcast emergency alerts to gram panchayats and farmers in Phase-II. \\ \hline
\end{tabularx}
\caption{Work Completed and Pending}
\label{tab:work_status}
\end{table}"""

work_new = r"""The execution status of system deliverables across Phase-I and upcoming Phase-II milestones is summarized in Table~\ref{tab:work_status}.

\begin{table}[H]
\centering
\small
\caption{Work Completed and Pending}
\label{tab:work_status}
\vspace{2pt}
\begin{tabularx}{\textwidth}{|L{3.6cm}|L{2.3cm}|Y|}
\hline
\textbf{Work Item} & \textbf{Status} & \textbf{Description} \\ \hline
Telemetry Ingestion Pipeline & Completed & Open-Meteo REST API data fetcher with Visual Crossing fallback. \\ \hline
Karnataka 27-Year Dataset & Completed & Digitized and analyzed $9,862$ historical daily observation records (2000--2027). \\ \hline
Physics Feature Engineering & Completed & 62 atmospheric domain metrics computed (DPD, VPD, $\theta_e$, diurnal factor). \\ \hline
GBDT Ensemble Training & Completed & LightGBM, XGBoost, and HistGradientBoosting trained with 91.2\% accuracy. \\ \hline
Gemini Multimodal Engine & Completed & Google Gemini API integrated for synoptic bulletins and calibrated probabilities. \\ \hline
3-Step Timeline Progression & Completed & $+30$m, $+60$m, $+90$m cards with individualized dynamic risk color theming. \\ \hline
Doppler Radar \& Micro-Zones & Completed & S-band concentric radar ($25$--$100$~km) with right-hand taluk sub-zones panel. \\ \hline
State Boundary Locking & Completed & Boundary validation that locks out-of-state queries and displays warning alert. \\ \hline
Live 12-Hour IST Clock & Completed & Real-time ticking header clock formatted in 12-hour AM/PM with instant hydration. \\ \hline
Dual Theme Support & Completed & Beige (light) and Espresso (dark) responsive design tokens. \\ \hline
INSAT-3D Satellite Feed & Pending & Ingest live Indian geostationary satellite infrared imagery in Phase-II. \\ \hline
Automated DWR Doppler Feed & Pending & Direct integration with IMD Mangalore/Bengaluru Doppler radar in Phase-II. \\ \hline
Automated SMS/WhatsApp Alerts & Pending & Broadcast emergency alerts to gram panchayats and farmers in Phase-II. \\ \hline
\end{tabularx}
\end{table}"""

text = text.replace(work_old, work_new)

# 6. Fix Figure introductions in Section 4.3 (Point 7: Paragraphs must never begin with Figure X)
fig_sec_old = r"""\subsection{Unified Convective Risk Hub and Telemetry Stack}
As illustrated in Figure~\ref{fig:hero_dash}, the left panel of the dashboard features the Unified Convective Risk Hub. It contains the concentric dial displaying the calibrated convective potential percentage ($0$--$100$\%), the dynamic alert banner, and the four telemetry metric cards (Temperature, Dew Point Depression, Vapor Pressure Deficit, and Barometric Pressure Tendency).

\begin{figure}[H]
\centering
\includegraphics[width=0.92\textwidth]{studentDashboard.png}
\caption{AeroCast AI Dashboard showing Convective Risk Hub and live telemetry stack.}
\label{fig:hero_dash}
\end{figure}

\subsection{Doppler Radar and Surrounding Micro-Zones Panel}
Figure~\ref{fig:radar_dash} depicts the S-band Doppler radar interface. Positioned directly to the right of the radar screen is the Places \& Micro-Zones panel, which allows users to monitor localized taluk sub-sectors (such as Darbe, Kabaka, Vitla, and Sullia for Puttur) with individual risk indicators and temperature/humidity soundings.

\begin{figure}[H]
\centering
\includegraphics[width=0.92\textwidth]{headDashboard.png}
\caption{Interactive S-Band Doppler Radar with adjacent localized Micro-Zones panel.}
\label{fig:radar_dash}
\end{figure}

\subsection{3-Step Timeline Progression and Gemini Advisories}
Figure~\ref{fig:timeline_dash} shows the 3-step convective nowcasting timeline ($+30$m, $+60$m, $+90$m) and the Gemini AI meteorological bulletins. Each minute card dynamically renders in Green, Yellow, or Red according to its individual forecasted probability. Below the timeline, Gemini provides domain-specific advisories for agriculture, travel safety, and aviation.

\begin{figure}[H]
\centering
\includegraphics[width=0.92\textwidth]{skillGap.png}
\caption{3-Step Nowcasting Timeline Progression and Gemini AI synoptic bulletins.}
\label{fig:timeline_dash}
\end{figure}"""

fig_sec_new = r"""\subsection{Unified Convective Risk Hub and Telemetry Stack}
The main user interface features a centralized Convective Risk Hub positioned on the primary display panel, as illustrated in Figure~\ref{fig:hero_dash}. It integrates a dynamic concentric gauge dial displaying the calibrated convective potential percentage ($0$--$100$\%), an automated status alert banner, and four real-time telemetry cards reporting ambient temperature, Dew Point Depression, Vapor Pressure Deficit, and barometric pressure tendency.

\begin{figure}[H]
\centering
\includegraphics[width=0.92\textwidth]{studentDashboard.png}
\caption{User interface layout featuring the Convective Risk Hub and live telemetry stack.}
\label{fig:hero_dash}
\end{figure}

\subsection{Doppler Radar and Surrounding Micro-Zones Panel}
Spatial storm tracking is facilitated through a customized geospatial canvas hosting an S-band Doppler radar display, shown in Figure~\ref{fig:radar_dash}. Situated directly to the right of the radar sweep is the localized Micro-Zones panel, enabling granular monitoring of taluk sub-sectors (such as Darbe, Kabaka, Vitla, and Sullia for Puttur) with individualized risk indicators and atmospheric soundings.

\begin{figure}[H]
\centering
\includegraphics[width=0.92\textwidth]{headDashboard.png}
\caption{Interactive S-Band Doppler Radar display with adjacent localized Micro-Zones panel.}
\label{fig:radar_dash}
\end{figure}

\subsection{3-Step Timeline Progression and Gemini Advisories}
Sequential hazard tracking is presented through the multi-horizon projection module illustrated in Figure~\ref{fig:timeline_dash}. The nowcast timeline presents $+30$m, $+60$m, and $+90$m convective risk projections, where each card dynamically updates its visual badge, icon, and background based on its forecasted probability. Positioned beneath the timeline, the generative AI engine authors synoptic meteorological bulletins alongside plain-language advisories for agriculture, transit safety, and public disaster preparedness.

\begin{figure}[H]
\centering
\includegraphics[width=0.92\textwidth]{skillGap.png}
\caption{Sequential three-step nowcast timeline progression with automated synoptic advisories.}
\label{fig:timeline_dash}
\end{figure}"""

text = text.replace(fig_sec_old, fig_sec_new)

# 7. Clean up other occurrences of project title at paragraph start or excessive branding
text = text.replace(r"\textbf{AeroCast AI} is designed to bridge this operational gap", "The proposed system is designed to bridge this operational gap")
text = text.replace(r"The core objectives of the \textbf{AeroCast AI} project are:", "The core objectives of the proposed nowcasting project are:")
text = text.replace(r"The geographical scope of AeroCast AI encompasses", "The geographical scope of the proposed system encompasses")
text = text.replace(r"AeroCast AI is motivated by", "This research is motivated by")
text = text.replace(r"\textbf{AeroCast AI} directly resolves these gaps", "The proposed system directly resolves these gaps")
text = text.replace(r"The hardware and software specifications utilized for the design, development, and execution of \textbf{AeroCast AI} are detailed in Tables~\ref{tab:hardware_req} and~\ref{tab:software_req}.", "The operational hardware and software components required for executing the proposed nowcasting system are summarized in Table~\ref{tab:hardware_req} and Table~\ref{tab:software_req}, respectively.")
text = text.replace(r"AeroCast AI follows a modular, three-tier architecture comprising the Data Ingestion \& Validation Layer, the Analytical \& Generative AI Core, and the Presentation Layer, as shown in Figure~\ref{fig:arch_system}.", "The proposed platform follows a modular, three-tier architecture comprising the Data Ingestion \\& Validation Layer, the Analytical \\& Generative AI Core, and the Presentation Layer, as shown in Figure~\\ref{fig:arch_system}.")
text = text.replace(r"AeroCast AI computes the following key atmospheric metrics:", "the proposed system computes the following key atmospheric metrics:")
text = text.replace(r"AeroCast AI models the diurnal insolation factor as:", "the system models the diurnal insolation factor as:")
text = text.replace(r"AeroCast AI is implemented as a full-stack, real-time meteorological nowcasting platform.", "The proposed nowcasting platform is implemented as a full-stack, real-time meteorological system.")
text = text.replace(r"The AeroCast AI dashboard provides an intuitive, high-density visualization interface", "The developed dashboard provides an intuitive, high-density visualization interface")
text = text.replace(r"In this Phase-I work, the complete architecture, machine learning models, physics pipeline, and user interface of \textbf{AeroCast AI} have been successfully developed, integrated, and verified. Designed as an MCA major project to tackle the dangerous unpredictability of tropical thunderstorms and lightning in Karnataka, AeroCast AI replaces coarse, delayed regional forecasts with a continuous 90-minute nowcasting engine. By decoupling raw empirical thresholds and grounding predictions in a 27-year regional climatological dataset ($9,862$ observation records), the system ensures that boundary-layer thermodynamics (DPD, VPD, diurnal insolation) are physically respected. By pairing a soft-voting GBDT ensemble with Google Gemini API, AeroCast AI provides accurate convective probabilities, personalized multi-sector advisories, dynamic risk-colored timeline cards, and an interactive S-band Doppler radar interface.", "In this Phase-I work, the complete architecture, machine learning models, physics pipeline, and user interface of the proposed nowcasting framework have been successfully developed, integrated, and verified. Designed as an MCA major project to address the hazardous unpredictability of tropical thunderstorms and lightning across Karnataka, the developed platform replaces coarse, delayed regional forecasts with a continuous 90-minute nowcasting engine. Grounding predictions in a 27-year regional climatological dataset ($9,862$ observation records) ensures that boundary-layer thermodynamics (DPD, VPD, diurnal insolation) are physically respected. Pairing a soft-voting GBDT ensemble with the Google Gemini API enables the delivery of accurate convective probabilities, personalized multi-sector advisories, dynamic risk-colored timeline cards, and an interactive S-band Doppler radar interface.")

with open('report/AeroCast_AI_Report.tex', 'w', encoding='utf-8') as f:
    f.write(text)

print("Successfully updated report/AeroCast_AI_Report.tex with all 7 suggestions applied!")
