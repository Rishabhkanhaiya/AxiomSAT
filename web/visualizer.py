"""
Official Visualizer Module for AxiomSAT.
Generates clean, academic-grade vector SVG visualizations (Light Theme / Zero Emojis).
"""

from typing import Dict, Any, Optional, List, Tuple
import networkx as nx

OFFICIAL_PALETTE = [
    "#2563EB",  # Royal Blue
    "#DC2626",  # Crimson Red
    "#059669",  # Forest Emerald
    "#D97706",  # Deep Amber
    "#7C3AED",  # Purple
    "#0891B2",  # Cyan Blue
    "#DB2777",  # Deep Rose
    "#4B5563",  # Slate
]


def generate_graph_svg(
    g: nx.Graph,
    title: str,
    node_colors: Optional[Dict[Any, str]] = None,
    default_color: str = "#2563EB",
    width: int = 380,
    height: int = 280
) -> str:
    """
    Renders an academic, publication-grade light mode SVG network graph.
    """
    if len(g) == 0:
        return f"<div style='color:#64748B; padding:12px; font-family:sans-serif;'>No active graph elements</div>"

    pos = nx.spring_layout(g, seed=42)
    padding = 40
    xs = [coord[0] for coord in pos.values()]
    ys = [coord[1] for coord in pos.values()]
    min_x, max_x = min(xs), max(xs)
    min_y, max_y = min(ys), max(ys)

    range_x = (max_x - min_x) if max_x != min_x else 1.0
    range_y = (max_y - min_y) if max_y != min_y else 1.0

    canvas_w = width - 2 * padding
    canvas_h = height - 2 * padding

    svg_coords = {}
    for node, (x, y) in pos.items():
        norm_x = padding + ((x - min_x) / range_x) * canvas_w
        norm_y = padding + ((y - min_y) / range_y) * canvas_h
        svg_coords[node] = (norm_x, norm_y)

    svg_lines = []
    svg_lines.append(f'<svg width="100%" height="{height}" viewBox="0 0 {width} {height}" style="background:#FFFFFF; border-radius:8px; border:1px solid #E2E8F0; overflow:hidden;" xmlns="http://www.w3.org/2000/svg">')

    # Header Bar
    svg_lines.append(f'<rect x="0" y="0" width="{width}" height="32" fill="#F1F5F9" stroke="#E2E8F0" stroke-width="1"/>')
    svg_lines.append(f'<text x="14" y="21" font-family="Inter, sans-serif" font-size="12" font-weight="700" fill="#0F172A">{title}</text>')
    svg_lines.append(f'<text x="{width - 14}" y="21" text-anchor="end" font-family="JetBrains Mono, monospace" font-size="11" font-weight="600" fill="#64748B">|V|={g.number_of_nodes()}  |E|={g.number_of_edges()}</text>')

    # Edges
    for u, v in g.edges():
        x1, y1 = svg_coords[u]
        x2, y2 = svg_coords[v]
        svg_lines.append(f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="#94A3B8" stroke-width="2" stroke-linecap="round" />')

    # Nodes
    for node in g.nodes():
        x, y = svg_coords[node]
        color = node_colors.get(node, default_color) if node_colors else default_color

        # Subtle shadow / ring
        svg_lines.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="17" fill="{color}" opacity="0.15" />')
        # Main Node circle
        svg_lines.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="14" fill="#FFFFFF" stroke="{color}" stroke-width="2.5"/>')
        # Label
        svg_lines.append(f'<text x="{x:.1f}" y="{y + 4.5:.1f}" text-anchor="middle" font-family="JetBrains Mono, monospace" font-size="11" font-weight="700" fill="{color}">{node}</text>')

    svg_lines.append('</svg>')
    return "".join(svg_lines)


def generate_dual_graph_html(g1: nx.Graph, g2: nx.Graph, mapping: Optional[Dict[Any, Any]] = None) -> str:
    """
    Renders two side-by-side SVG graphs with matching color-coded nodes.
    """
    color_g1 = {}
    color_g2 = {}

    if mapping:
        for idx, (u, v) in enumerate(mapping.items()):
            c = OFFICIAL_PALETTE[idx % len(OFFICIAL_PALETTE)]
            color_g1[u] = c
            color_g2[v] = c
    else:
        color_g1 = {n: "#2563EB" for n in g1.nodes()}
        color_g2 = {n: "#4F46E5" for n in g2.nodes()}

    svg1 = generate_graph_svg(g1, "Graph G1 (Reference)", color_g1, default_color="#2563EB")
    svg2 = generate_graph_svg(g2, "Graph G2 (Target)", color_g2, default_color="#4F46E5")

    html = f"""
    <div style="display:flex; gap:16px; width:100%; justify-content:center; flex-wrap:wrap;">
        <div style="flex:1; min-width:300px;">{svg1}</div>
        <div style="flex:1; min-width:300px;">{svg2}</div>
    </div>
    """
    return html


def generate_miter_diagram_svg(c1_name: str, c2_name: str, status_is_unsat: Optional[bool] = None) -> str:
    """
    Generates an official light-mode hardware schematic of the Miter Circuit.
    """
    badge_bg = "#ECFDF5" if status_is_unsat is True else ("#FEF2F2" if status_is_unsat is False else "#F1F5F9")
    badge_border = "#059669" if status_is_unsat is True else ("#DC2626" if status_is_unsat is False else "#94A3B8")
    badge_color = "#047857" if status_is_unsat is True else ("#B91C1C" if status_is_unsat is False else "#475569")
    badge_text = "VERIFIED EQUIVALENT [UNSAT]" if status_is_unsat is True else ("DISCREPANCY DETECTED [SAT]" if status_is_unsat is False else "READY FOR EVALUATION")

    svg = f"""
    <svg width="100%" height="220" viewBox="0 0 680 220" style="background:#FFFFFF; border-radius:8px; border:1px solid #E2E8F0;" xmlns="http://www.w3.org/2000/svg">
        <!-- Input Block -->
        <rect x="20" y="70" width="90" height="80" rx="6" fill="#F8FAFC" stroke="#2563EB" stroke-width="2"/>
        <text x="65" y="105" text-anchor="middle" font-family="Inter, sans-serif" font-size="12" font-weight="700" fill="#1E3A8A">PRIMARY</text>
        <text x="65" y="122" text-anchor="middle" font-family="Inter, sans-serif" font-size="11" font-weight="600" fill="#64748B">INPUTS [X]</text>

        <!-- Bus Lines -->
        <path d="M 110 100 L 160 100 L 160 55 L 200 55" stroke="#2563EB" stroke-width="2" fill="none"/>
        <path d="M 110 120 L 160 120 L 160 165 L 200 165" stroke="#2563EB" stroke-width="2" fill="none"/>

        <!-- Circuit 1 -->
        <rect x="200" y="30" width="170" height="55" rx="6" fill="#F8FAFC" stroke="#4F46E5" stroke-width="2"/>
        <text x="285" y="62" text-anchor="middle" font-family="Inter, sans-serif" font-size="12" font-weight="700" fill="#1E1B4B">C1: {c1_name[:18]}</text>

        <!-- Circuit 2 -->
        <rect x="200" y="135" width="170" height="55" rx="6" fill="#F8FAFC" stroke="#4F46E5" stroke-width="2"/>
        <text x="285" y="167" text-anchor="middle" font-family="Inter, sans-serif" font-size="12" font-weight="700" fill="#1E1B4B">C2: {c2_name[:18]}</text>

        <!-- Lines to XOR -->
        <path d="M 370 58 L 420 58 L 440 95" stroke="#4F46E5" stroke-width="2" fill="none"/>
        <path d="M 370 162 L 420 162 L 440 125" stroke="#4F46E5" stroke-width="2" fill="none"/>

        <!-- XOR Miter Gate -->
        <g transform="translate(435, 80)">
            <path d="M 10 0 C 25 15, 25 35, 10 50 C 35 50, 50 35, 60 25 C 50 15, 35 0, 10 0 Z" fill="#F8FAFC" stroke="#0F172A" stroke-width="2"/>
            <path d="M 3 0 C 18 15, 18 35, 3 50" fill="none" stroke="#0F172A" stroke-width="1.8"/>
            <text x="28" y="30" font-family="Inter, sans-serif" font-size="11" font-weight="800" fill="#0F172A">XOR</text>
        </g>

        <!-- Output Line -->
        <line x1="495" y1="105" x2="530" y2="105" stroke="#0F172A" stroke-width="2" />

        <!-- Status Badge -->
        <rect x="530" y="85" width="135" height="40" rx="6" fill="{badge_bg}" stroke="{badge_border}" stroke-width="1.5"/>
        <text x="597" y="110" text-anchor="middle" font-family="JetBrains Mono, monospace" font-size="9" font-weight="700" fill="{badge_color}">{badge_text}</text>
    </svg>
    """
    return svg
