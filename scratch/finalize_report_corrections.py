import re

with open('report/AeroCast_AI_Report.tex', 'r', encoding='utf-8') as f:
    c = f.read()

# 1. Update Proposed System row in Table 2.1
c = c.replace(
    r'\textbf{Proposed System (AeroCast AI)} & \textbf{2026} & \textbf{Unified 27-yr Karnataka climatology, 62-feat GBDT ensemble, and Gemini LLM synoptic bulletins.} & \textbf{Pro:} 0--90m nowcast, zero nocturnal false alarms, interactive radar UI. \newline \textbf{Con:} Bounded to Karnataka boundary; multi-state in Ph-II. \\ \hline',
    r'\textbf{Proposed Nowcasting System} & \textbf{2026} & \textbf{Unified 27-yr Karnataka climatology, 62-feat GBDT ensemble, and Gemini LLM synoptic bulletins.} & \textbf{Pro:} 0--90m nowcast, zero nocturnal false alarms, interactive radar UI. \newline \textbf{Con:} Bounded to Karnataka boundary; multi-state in Ph-II. \\ \hline'
)

# 2. Section 2.3 citations cleanup to avoid out-of-order parenthetical callouts
old_gap = r'While recent literature demonstrates significant progress in computer vision-based radar extrapolation (Rayudu et al., 2025 \cite{rayudu2025prediction}; Kim et al., 2024 \cite{kim2024improvements}) and machine learning lightning prediction (Kumar et al., 2026 \cite{kumar2026enhancing}; Chen et al., 2026 \cite{chen2026clka}; Toropova et al., 2022 \cite{toropova2022characteristics}), three critical research gaps remain unaddressed in regional operational meteorology:'
new_gap = r'While the surveyed literature demonstrates significant progress in computer vision-based radar extrapolation and machine learning lightning prediction, three critical research gaps remain unaddressed in regional operational meteorology:'
c = c.replace(old_gap, new_gap)

# 3. Section 3.1.2 figure: use proposed_system_block_diagram.png
c = c.replace(
    r'''\begin{figure}[H]
\centering
\includegraphics[width=0.92\textwidth]{proposed_system_architecture.png}
\caption{Block diagram and data processing pipeline of the proposed convective nowcasting system.}
\label{fig:proposed_system}
\end{figure}''',
    r'''\begin{figure}[H]
\centering
\includegraphics[width=0.92\textwidth]{proposed_system_block_diagram.png}
\caption{High-level conceptual block diagram and data processing pipeline of the proposed convective nowcasting system.}
\label{fig:proposed_system}
\end{figure}'''
)

# 4. Spacing on hardware/software table references
c = re.sub(r'Table~\s*\\ref\{tab:hardware_req\}\s+and\s+Table~\s*\\ref\{tab:software_req\}',
           r'Table~\\ref{tab:hardware_req} and Table~\\ref{tab:software_req}', c)

# 5. Section 3.3 figure: use proposed_system_architecture.png
c = c.replace(
    r'''\begin{figure}[H]
\centering
\includegraphics[width=0.92\textwidth]{architecture.png}
\caption{Three-tier architecture of the AeroCast AI nowcasting system.}
\label{fig:arch_system}
\end{figure}''',
    r'''\begin{figure}[H]
\centering
\includegraphics[width=0.92\textwidth]{proposed_system_architecture.png}
\caption{Three-tier architecture of the proposed nowcasting system.}
\label{fig:arch_system}
\end{figure}'''
)

# 6. Stray backticks and formatting fixes
c = c.replace(", `and retrieves", ", and retrieves")
c = c.replace(r"``N/A\'\'.", "``N/A''.")
c = c.replace(r"(e.g., `$01:28:52", r"(e.g., $01:28:52")
c = c.replace(r"alert), `avoiding the false", r"alert), avoiding the false")
c = c.replace(r"``Partly Cloudy with Moderate Convective Buildup\'\'", r"``Partly Cloudy with Moderate Convective Buildup''")
c = c.replace("daytime solar heating. the system models", "daytime solar heating. The system models")

# Running header adjustment
c = c.replace(r"\fancyhead[L]{\small AeroCast AI}", r"\fancyhead[L]{\small AI-Driven Convective Nowcasting}")

with open('report/AeroCast_AI_Report.tex', 'w', encoding='utf-8') as f:
    f.write(c)

print('File updated successfully.')
