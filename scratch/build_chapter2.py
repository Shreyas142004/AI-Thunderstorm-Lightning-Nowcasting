import re
from pathlib import Path

# Load bibitems from AeroCast_AI_Report.tex
with open('report/AeroCast_AI_Report.tex', encoding='utf-8') as f:
    tex = f.read()

bib_pattern = r'\\bibitem\{([^}]+)\}\s*(.*?)(?=\\bibitem|\s*\\end\{thebibliography\})'
matches = list(re.finditer(bib_pattern, tex, re.DOTALL))

# Detailed dictionary of all 25 papers with exact title, author, year, doi, journal, description, pros, cons
papers_data = [
    {
        "key": "tian2026dual",
        "year": 2026,
        "title": "A Dual-Weighted Loss Function for Lightning Nowcasting",
        "authors": "J.~Tian, W.~Han, H.~Sun, Y.~Li, G.~Xu, X.~Meng, and Q.~Ma",
        "journal": "Atmospheric and Oceanic Science Letters",
        "volume": "vol. 19, art. no. 100778",
        "doi": "10.1016/j.aosl.2026.100778",
        "desc": "Dual-weighted loss formulation penalizing false negatives in high-intensity convective storm cores to counter severe pixel imbalance.",
        "pros": "Effectively mitigates severe class imbalance between quiescent and active convective storm pixels.",
        "cons": "Optimized strictly for loss calculation; requires pairing with external spatiotemporal backbones."
    },
    {
        "key": "chen2026clka",
        "year": 2026,
        "title": "CLKA-LPO: A CNN-LSTM-KAN Neural Network for Lightning Potential and Flash Rate Prediction Based on Atmospheric Physical Parameters",
        "authors": "H.~Chen, T.~Xu, Y.~Du, Q.~Yin, Y.~Zhu, Z.~Luo, Y.~Song, M.~Xia, and S.~Zhao",
        "journal": "Atmospheric and Oceanic Science Letters",
        "volume": "vol. 19, art. no. 100679",
        "doi": "10.1016/j.aosl.2025.100679",
        "desc": "Deep architecture coupling CNN-LSTM with Kolmogorov-Arnold Networks (KAN) to map sounding parameters to flash density.",
        "pros": "Strong non-linear physical mapping of vertical atmospheric sounding profiles to lightning rates.",
        "cons": "High theoretical complexity; lacks operational spatial mapping and user-facing decision dashboard."
    },
    {
        "key": "kumar2026enhancing",
        "year": 2026,
        "title": "Enhancing the Forecasting of Lightning Density Over Northern India: An Ensemble and Deep Learning Models Approach",
        "authors": "P.~Kumar, R.~K. Singh, and M.~Maurya",
        "journal": "Physics and Chemistry of the Earth, Parts A/B/C",
        "volume": "vol. 138, art. no. 104702",
        "doi": "10.1016/j.pce.2026.104702",
        "desc": "Comparative evaluation of XGBoost, LightGBM, and Deep Neural Networks on atmospheric soundings across northern India.",
        "pros": "Demonstrates decisive performance superiority of tree ensembles over deep networks on tabular soundings.",
        "cons": "Operates on broad seasonal and synoptic scales; lacks short-range 0--90 minute nowcast trajectories."
    },
    {
        "key": "wang2026infrared",
        "year": 2026,
        "title": "Infrared Brightness Temperature-Based Indicators for Identifying Thunderstorm Clouds: Insights From FY-4A Satellite Observations",
        "authors": "C.~Wang, R.~Jiang, J.~Xia, Y.~Wu, H.~Shi, F.~Li, and X.~Xia",
        "journal": "Atmospheric and Oceanic Science Letters",
        "volume": "vol. 19, art. no. 100658",
        "doi": "10.1016/j.aosl.2025.100658",
        "desc": "Split-window infrared brightness temperature difference analysis for early detection of intensifying convective clouds.",
        "pros": "Provides rapid pre-convective cloud-top cooling indicators prior to surface storm initiation.",
        "cons": "Subject to parallax errors in complex topography; lacks surface boundary-layer thermodynamic checks."
    },
    {
        "key": "li2026nowcasting",
        "year": 2026,
        "title": "Nowcasting of Cloud-to-Ground Lightning Location and Frequency Based on a Deep Learning Technique",
        "authors": "F.~Li, J.~Li, S.~Gu, Y.~Wang, Z.~Li, L.~Zhang, Z.~Liu, B.~Bai, and Z.~Jiang",
        "journal": "Atmospheric and Oceanic Science Letters",
        "volume": "vol. 19, art. no. 100607",
        "doi": "10.1016/j.aosl.2025.100607",
        "desc": "Spatial attention Conv-GRU network predicting lightning strike density grids and discharge frequencies.",
        "pros": "Spatial attention mechanism prioritizes active updrafts over dissipating anvil debris.",
        "cons": "Heavy computational footprint during multi-step inference; lacks plain-language advisory translation."
    },
    {
        "key": "li2026correlation",
        "year": 2026,
        "title": "Research on the Correlation Between Meteorological Radar Echo Characteristics and Lightning Warning Technology",
        "authors": "Z.~Li, H.~Zhang, J.~Hu, Y.~Zhang, and J.~Yao",
        "journal": "Atmospheric and Oceanic Science Letters",
        "volume": "vol. 19, art. no. 100649",
        "doi": "10.1016/j.aosl.2025.100649",
        "desc": "Empirical correlation between vertical radar echo volume (>=40 dBZ above freezing level) and lightning strokes.",
        "pros": "Establishes direct physical radar reflectivity criteria for cloud-to-ground electrical discharge warning.",
        "cons": "Dependent on high-bandwidth Doppler radar grids; susceptible to beam blockage in mountain valleys."
    },
    {
        "key": "zhang2025lightning",
        "year": 2025,
        "title": "A Lightning Augmented Recurrent Nowcasting Model Based on Self-Supervised Learning and Multi-Modal Fusion Method",
        "authors": "Y.~Zhang, H.~Wang, Z.~Chen, and X.~Liu",
        "journal": "Atmospheric Research",
        "volume": "vol. 317, art. no. 108089",
        "doi": "10.1016/j.atmosres.2025.108089",
        "desc": "Self-supervised spatiotemporal recurrent framework fusing optical satellite imagery with lightning strike streams.",
        "pros": "Self-supervised pre-training significantly improves convective representation learning.",
        "cons": "Demands high GPU cluster capacity for inference; not optimized for low-latency web deployment."
    },
    {
        "key": "ghosh2025assessment",
        "year": 2025,
        "title": "Assessment of the Indian Lightning Location Network (ILLN) Using Ground-Based and Satellite Observations",
        "authors": "K.~K. Ghosh, D.~R. Pattanaik, and S.~Soni",
        "journal": "Atmospheric Research",
        "volume": "vol. 316, art. no. 108069",
        "doi": "10.1016/j.atmosres.2025.108069",
        "desc": "Empirical assessment of ILLN ground sensor network efficiency against spaceborne optical lightning imagers over India.",
        "pros": "Verifies high cloud-to-ground detection efficiency (>88%) across Indian landmass.",
        "cons": "Identifies significant terrain-induced detection attenuation across Western Ghats valleys."
    },
    {
        "key": "sharma2025insat",
        "year": 2025,
        "title": "Leveraging INSAT-3D Indian Geostationary Satellite for Advanced Lightning Detection and Analysis",
        "authors": "R.~Sharma, P.~K. Singh, and A.~K. Mitra",
        "journal": "Geophysical Research Letters",
        "volume": "vol. 52, no. 3, art. no. e2024GL112764",
        "doi": "10.1029/2024GL112764",
        "desc": "Thermal infrared channel tracking on INSAT-3D for detecting rapid cloud-top cooling and convective storm initiation.",
        "pros": "Demonstrates high utility of indigenous INSAT-3D satellite imagery for pre-convective monitoring.",
        "cons": "Coarse 4 km infrared resolution; lacks machine learning calibration against local surface AWS."
    },
    {
        "key": "rayudu2025prediction",
        "year": 2025,
        "title": "Prediction of Thunderstorm Evolution Using Deep Learning Models With Doppler Weather Radar Observations Over Southern Part of India",
        "authors": "S.~S.~S. Rayudu, P.~V.~S. Raju, and R.~Satyanarayana",
        "journal": "Dynamics of Atmospheres and Oceans",
        "volume": "vol. 109, art. no. 101566",
        "doi": "10.1016/j.dynatmoce.2025.101566",
        "desc": "ConvLSTM and PredRNN spatiotemporal models applied to DWR reflectivity to predict thunderstorm cell evolution over South India.",
        "pros": "Effectively models storm cell morphology, translation, and decay over southern India.",
        "cons": "Radar-dependent; does not incorporate surface thermodynamic indices (DPD, VPD) or diurnal checks."
    },
    {
        "key": "le2024autocorrelated",
        "year": 2024,
        "title": "An Autocorrelated Conditioned Latin Hypercube Method for Temporal or Spatial Sampling and Predictions",
        "authors": "V.~H. Le and R.~Vargas",
        "journal": "Computers & Geosciences",
        "volume": "vol. 184, art. no. 105539",
        "doi": "10.1016/j.cageo.2024.105539",
        "desc": "Conditioned Latin hypercube sampling algorithm tailored for preserving temporal and spatial autocorrelation in meteorological series.",
        "pros": "Preserves spatiotemporal autocorrelation and physical feature variance during data subsampling.",
        "cons": "Focused primarily on sampling methodology rather than operational end-to-end nowcast deployment."
    },
    {
        "key": "rombeek2024exploiting",
        "year": 2024,
        "title": "Exploiting Radar Polarimetry for Nowcasting Thunderstorm Hazards Using Deep Learning",
        "authors": "N.~Rombeek, J.~Leinonen, and U.~Hamann",
        "journal": "Natural Hazards and Earth System Sciences",
        "volume": "vol. 24, no. 1, pp. 133--144",
        "doi": "10.5194/nhess-24-133-2024",
        "desc": "Evaluation of dual-polarization Doppler radar variables (Z_DR, K_DP) within deep convolutional nowcasting models.",
        "pros": "Proves polarimetric differential reflectivity significantly improves hydrometeor classification.",
        "cons": "Dual-polarization radar telemetry is not uniformly available across regional Indian stations."
    },
    {
        "key": "kim2024improvements",
        "year": 2024,
        "title": "Improvements in Deep Learning-Based Precipitation Nowcasting Using Major Atmospheric Factors With Radar Rain Rate",
        "authors": "W.~Kim, C.-H. Jeong, and S.~Kim",
        "journal": "Computers & Geosciences",
        "volume": "vol. 184, art. no. 105529",
        "doi": "10.1016/j.cageo.2024.105529",
        "desc": "Encoder-forecaster neural network fusing surface AWS observations (temperature, humidity, pressure) with radar rain rates.",
        "pros": "Proves integrating surface thermodynamics significantly reduces nowcast degradation beyond 30 minutes.",
        "cons": "Remains dependent on high-density radar grids; lacks nocturnal boundary-layer stability damping."
    },
    {
        "key": "cintineo2024probsevere",
        "year": 2024,
        "title": "ProbSevere Version 3: Improved Exploitation of Data Fusion and Machine Learning for Nowcasting Severe Weather",
        "authors": "J.~L. Cintineo, M.~J. Pavolonis, and J.~M. Sieglaff",
        "journal": "Weather and Forecasting",
        "volume": "vol. 39, no. 11, pp. 2045--2068",
        "doi": "10.1175/WAF-D-24-0076.1",
        "desc": "NOAA operational severe weather nowcasting system using Gradient Boosted Decision Trees for multiscale sensor data fusion.",
        "pros": "Provides operational benchmark for calibrated probabilistic severe storm alerts.",
        "cons": "Tightly coupled to United States NWS radar infrastructure; not calibrated for tropical orography."
    },
    {
        "key": "soni2023machine",
        "year": 2023,
        "title": "A Machine Learning Approach for Prediction of Seasonal Lightning Density in Different Lightning Regions of India",
        "authors": "V.~K. Soni, S.~Karmakar, and K.~K. Ghosh",
        "journal": "International Journal of Climatology",
        "volume": "vol. 43, no. 6, pp. 2835--2854",
        "doi": "10.1002/joc.8005",
        "desc": "Random Forest and SVM classifiers analyzing thermodynamic parameters (CAPE, total precipitable water) across Indian climate zones.",
        "pros": "Confirms strong geographical dependency of lightning activity on thermodynamic energy across India.",
        "cons": "Designed for seasonal climatological forecasts; does not support real-time 0--90 minute nowcasting."
    },
    {
        "key": "song2023lightning",
        "year": 2023,
        "title": "Lightning Nowcasting With Aerosol-Informed Machine Learning and Satellite-Enriched Dataset",
        "authors": "G.~Song, S.~Li, and J.~Xing",
        "journal": "npj Climate and Atmospheric Science",
        "volume": "vol. 6, art. no. 126",
        "doi": "10.1038/s41612-023-00451-x",
        "desc": "Aerosol-informed LightGBM tree ensemble model achieving 94.3% accuracy for hourly lightning hazard prediction.",
        "pros": "Achieves high classification accuracy (94.3%) by incorporating aerosol and multi-sensor datasets.",
        "cons": "Trained on continental US data; does not account for South Asian monsoon moisture dynamics."
    },
    {
        "key": "lu2023mcgln",
        "year": 2023,
        "title": "MCGLN: A Multimodal ConvLSTM-GAN Framework for Lightning Nowcasting Utilizing Multi-Source Spatiotemporal Data",
        "authors": "M.~Lu, C.~Jin, M.~Yu, Q.~Zhang, H.~Liu, Z.~Huang, and T.~Dong",
        "journal": "SSRN Electronic Journal",
        "volume": "Preprint",
        "doi": "10.2139/ssrn.4510991",
        "desc": "Generative Adversarial Network architecture paired with ConvLSTM to synthesize multimodal radar and lightning grids.",
        "pros": "Adversarial training maintains sharp storm edge gradients and mitigates blurring over longer lead times.",
        "cons": "Training instability common to GANs; demands massive computational resources for operational inference."
    },
    {
        "key": "das2023impact",
        "year": 2023,
        "title": "The Impact of Indian Radar and Lightning Data Assimilation on the Short-Range Forecasts of Heavy Rainfall Events",
        "authors": "M.~Das, S.~K. Roy~Bhowmik, and A.~K. Das",
        "journal": "Quarterly Journal of the Royal Meteorological Society",
        "volume": "vol. 150, no. 758, pp. 320--342",
        "doi": "10.1002/qj.4623",
        "desc": "3D-Var assimilation of Doppler weather radar reflectivity and ground lightning data into numerical prediction models.",
        "pros": "Significantly improves precipitation location and intensity accuracy in numerical forecasts.",
        "cons": "High computational cost; assimilation and execution cycle lags behind immediate nowcasting horizons."
    },
    {
        "key": "leinonen2023multihazard",
        "year": 2023,
        "title": "Thunderstorm Nowcasting With Deep Learning: A Multi-Hazard Data Fusion Model",
        "authors": "J.~Leinonen, U.~Hamann, U.~Germann, and J.~R. Mecikalski",
        "journal": "Geophysical Research Letters",
        "volume": "vol. 50, no. 8, art. no. e2022GL101626",
        "doi": "10.1029/2022GL101626",
        "desc": "Deep multimodal neural network fusing radar, satellite, and lightning observations for multi-hazard convective prediction.",
        "pros": "Demonstrates comprehensive multi-hazard predictive capability across complex alpine terrain.",
        "cons": "Extreme GPU hardware requirement; lacks public web-accessible decision dashboard for rural sectors."
    },
    {
        "key": "toropova2022characteristics",
        "year": 2022,
        "title": "Characteristics of Thunderstorms During the Monsoon and Post-Monsoon Seasons in India",
        "authors": "M.~L. Toropova, A.~A. Sin'kevich, S.~Pawar, V.~Gopalakrishnan, and Yu.~P. Mikhailovskii",
        "journal": "Russian Meteorology and Hydrology",
        "volume": "vol. 47, no. 8, pp. 620--628",
        "doi": "10.3103/S1068373922080088",
        "desc": "Empirical investigation of over 2,500 convective clouds and 5,000 electrical discharges over Gadag, Karnataka.",
        "pros": "Provides localized Karnataka empirical dataset establishing radar reflectivity and lightning surges.",
        "cons": "Retrospective statistical study; lacks an automated predictive machine learning pipeline."
    },
    {
        "key": "leinonen2022seamless",
        "year": 2022,
        "title": "Seamless Lightning Nowcasting With Recurrent-Convolutional Deep Learning",
        "authors": "J.~Leinonen, U.~Hamann, and U.~Germann",
        "journal": "Artificial Intelligence for the Earth Systems",
        "volume": "vol. 1, no. 4, art. no. e220043",
        "doi": "10.1175/AIES-D-22-0043.1",
        "desc": "Recurrent-convolutional neural network generating seamless 60-minute lightning nowcasts over complex topography.",
        "pros": "Smoothly bridges the gap between observation extrapolation and numerical model initiation.",
        "cons": "Predictive skill degrades rapidly beyond 60 minutes without boundary-layer thermodynamic data."
    },
    {
        "key": "sibolla2021determining",
        "year": 2021,
        "title": "Determining Real-Time Patterns of Lightning Strikes From Sensor Observations",
        "authors": "B.~H. Sibolla, T.~Van~Zyl, and S.~Coetzee",
        "journal": "Journal of Geovisualization and Spatial Analysis",
        "volume": "vol. 5, art. no. 4",
        "doi": "10.1007/s41651-020-00070-7",
        "desc": "Graph-theoretic spatiotemporal clustering algorithm mapping real-time lightning strike trajectories for visualization.",
        "pros": "Provides intuitive graph-based spatial clustering and event trajectory tracking.",
        "cons": "Post-event clustering mechanism; lacks forward predictive convective modeling."
    },
    {
        "key": "leinonen2021nowcasting",
        "year": 2021,
        "title": "Nowcasting Thunderstorm Hazards Using Machine Learning: The Impact of Data Sources on Performance",
        "authors": "J.~Leinonen, U.~Hamann, Urs Germann, and J.~R. Mecikalski",
        "journal": "Natural Hazards and Earth System Sciences",
        "volume": "vol. 21, pp. 577--599",
        "doi": "10.5194/nhess-2021-171",
        "desc": "Systematic variable importance study evaluating 106 multi-source predictors for GBDT thunderstorm nowcasts.",
        "pros": "Demonstrates that surface moisture soundings and radar data are the primary drivers of nowcasting skill.",
        "cons": "Theoretical feature analysis; lacks deployment into a live, interactive meteorological dashboard."
    },
    {
        "key": "luo2021pfst",
        "year": 2021,
        "title": "PFST-LSTM: A SpatioTemporal LSTM Model With Pseudoflow Prediction for Precipitation Nowcasting",
        "authors": "C.~Luo, X.~Li, and Y.~Ye",
        "journal": "IEEE Journal of Selected Topics in Applied Earth Observations and Remote Sensing",
        "volume": "vol. 14, pp. 843--854",
        "doi": "10.1109/JSTARS.2020.3040648",
        "desc": "Pseudoflow spatiotemporal LSTM network modeling non-rigid cloud deformation and advection vectors.",
        "pros": "Improves radar echo extrapolation by modeling non-rigid cloud motion and expansion.",
        "cons": "Prone to cumulative spatial blur over extended lead times; ignores surface atmospheric physics."
    },
    {
        "key": "goyal2017satellite",
        "year": 2017,
        "title": "Satellite-Based Technique for Nowcasting of Thunderstorms Over Indian Region",
        "authors": "S.~Goyal, A.~Kumar, M.~Mohapatra, L.~S. Rathore, S.~K. Dube, R.~Saxena, and R.~K. Giri",
        "journal": "Journal of Earth System Science",
        "volume": "vol. 126, art. no. 79",
        "doi": "10.1007/s12040-017-0859-2",
        "desc": "Operational thunderstorm tracking using INSAT-3D thermal infrared imagery and ForTraCC tracking over India.",
        "pros": "Pioneered automated satellite cloud cluster tracking for thunderstorm warnings across India.",
        "cons": "High false alarm rate due to absence of boundary-layer thermodynamic soundings and ML classification."
    }
]

print(f"Total papers configured: {len(papers_data)}")
for i, p in enumerate(papers_data, 1):
    print(f"[{i:2d}] {p['year']} | {p['key']} | {p['title'][:55]}")
