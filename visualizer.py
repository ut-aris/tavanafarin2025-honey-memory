"""
Visualization functions for Clinic B hexagonal grid task analysis.

This module provides utilities to visualize trial patterns and participant responses
from the visuospatial working memory task.
"""

import ast
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import RegularPolygon


def _maybe_eval(x):
    """Convert string representation of list/tuple to actual object if needed."""
    if isinstance(x, str) and (x.startswith("[") or x.startswith("(")):
        return ast.literal_eval(x)
    return x


def plot_trial_pattern(
    trial_row,
    ax=None,
    hex_radius=38.4,
    show_clicks=False,
    figsize=(8, 5),
    dpi=120,
):
    """
    Visualize a single trial's hexagonal pattern.

    Parameters:
    -----------
    trial_row : pandas.Series
        A row from clinic_b_df containing trial data
    ax : matplotlib axis, optional
        Axis to plot on. Creates new figure if None.
    hex_radius : float
        Radius of hexagons in pixels
    show_clicks : bool
        Whether to overlay participant's click responses
    figsize : tuple
        Figure size if creating new figure
    dpi : int
        Resolution if creating new figure

    Returns:
    --------
    ax : matplotlib axis
    """
    if ax is None:
        fig, ax = plt.subplots(figsize=figsize, dpi=dpi)

    # Color scheme
    colors = {
        "background": "#eeeeee",
        "target": "#ffff66",  # Yellow for targets
        "gray": "#bbbbbb",  # Gray for disabled cells
        "white": "#ffffff",  # White for available non-targets
        "correct": "#66ff66",  # Green for correct clicks
        "incorrect": "#ff9696",  # Red for incorrect clicks
    }

    # Parse trial data
    all_positions = _maybe_eval(trial_row["all_hex_positions_xy"])
    targets = set(_maybe_eval(trial_row["target_hex_indices"]))
    grays = set(_maybe_eval(trial_row["gray_hex_indices"]))
    whites = set(_maybe_eval(trial_row["white_hex_indices"]))

    # Draw hexagonal grid
    for idx, (x, y) in enumerate(all_positions):
        if idx in targets:
            face_color, edge_color = colors["target"], "black"
        elif idx in grays:
            face_color, edge_color = colors["gray"], "none"
        elif idx in whites:
            face_color, edge_color = colors["white"], "black"
        else:
            face_color, edge_color = colors["background"], "black"

        hexagon = RegularPolygon(
            (x, y),
            numVertices=6,
            radius=hex_radius,
            orientation=0,
            facecolor=face_color,
            edgecolor=edge_color,
            linewidth=0.8 if edge_color != "none" else 0,
        )
        ax.add_patch(hexagon)

    # Overlay clicks if requested
    if show_clicks:
        correct_clicks = _maybe_eval(trial_row.get("correct_click_positions_xy", []))
        incorrect_clicks = _maybe_eval(
            trial_row.get("incorrect_click_positions_xy", [])
        )
        click_sequence = _maybe_eval(trial_row.get("click_sequence_positions_xy", []))

        # Draw click markers
        for x, y in incorrect_clicks:
            marker = RegularPolygon(
                (x, y),
                numVertices=6,
                radius=hex_radius * 0.6,
                facecolor=colors["incorrect"],
                edgecolor="darkred",
                linewidth=2,
                alpha=0.8,
            )
            ax.add_patch(marker)

        for x, y in correct_clicks:
            marker = RegularPolygon(
                (x, y),
                numVertices=6,
                radius=hex_radius * 0.6,
                facecolor=colors["correct"],
                edgecolor="darkgreen",
                linewidth=2,
                alpha=0.8,
            )
            ax.add_patch(marker)

        # Draw click sequence path
        if click_sequence and len(click_sequence) > 1:
            xs, ys = zip(*click_sequence)
            ax.plot(xs, ys, "k-", linewidth=2, alpha=0.4, zorder=1)

        # Add statistics annotation
        correctness = trial_row["click_correctness_sequence"]
        accuracy = sum(correctness) / len(correctness) if correctness else 0
        n_clicks = len(correctness)

        stats_text = f"Clicks: {n_clicks}\nAccuracy: {accuracy:.1%}"
        ax.text(
            0.02,
            0.98,
            stats_text,
            transform=ax.transAxes,
            fontsize=11,
            verticalalignment="top",
            bbox=dict(boxstyle="round", facecolor="white", alpha=0.8),
        )

    # Formatting
    ax.set_aspect("equal")
    ax.axis("off")

    xs, ys = zip(*all_positions)
    ax.set_xlim(min(xs) - hex_radius * 1.5, max(xs) + hex_radius * 1.5)
    ax.set_ylim(max(ys) + hex_radius * 1.5, min(ys) - hex_radius * 1.5)

    # Add title
    title = f"Participant: {trial_row['participant_id']}\n"
    title += f"Trial {trial_row['trial_number']} | Difficulty: {trial_row['level']}"
    ax.set_title(title, fontsize=12, pad=10)

    return ax


def plot_multiple_trials(df, n_trials=6, show_clicks=True, random_sample=True, seed=42):
    """
    Plot multiple trials in a grid layout.

    Parameters:
    -----------
    df : pandas.DataFrame
        The clinic_b_df dataframe
    n_trials : int
        Number of trials to plot
    show_clicks : bool
        Whether to show participant responses
    random_sample : bool
        If True, randomly sample trials. If False, take first n_trials.
    seed : int
        Random seed for reproducibility

    Returns:
    --------
    fig : matplotlib figure
    """
    if random_sample:
        np.random.seed(seed)
        sample_trials = df.sample(n=min(n_trials, len(df)))
    else:
        sample_trials = df.head(n_trials)

    # Calculate grid dimensions
    n_cols = min(3, n_trials)
    n_rows = (n_trials + n_cols - 1) // n_cols

    fig, axes = plt.subplots(n_rows, n_cols, figsize=(8 * n_cols, 5 * n_rows), dpi=100)

    # Handle single subplot case
    if n_trials == 1:
        axes = np.array([axes])
    axes = axes.flatten() if n_trials > 1 else axes

    for idx, (_, trial) in enumerate(sample_trials.iterrows()):
        if idx < len(axes):
            plot_trial_pattern(trial, ax=axes[idx], show_clicks=show_clicks)

    # Hide unused subplots
    for idx in range(len(sample_trials), len(axes)):
        axes[idx].axis("off")

    plt.tight_layout()
    return fig


def compare_adhd_vs_control(df, difficulty_level=None, n_each=3, seed=42):
    """
    Compare trial patterns between ADHD and Control groups side by side.

    Parameters:
    -----------
    df : pandas.DataFrame
        The clinic_b_df dataframe
    difficulty_level : int, optional
        Specific difficulty level to filter. If None, uses all levels.
    n_each : int
        Number of trials to show from each group
    seed : int
        Random seed for reproducibility

    Returns:
    --------
    fig : matplotlib figure
    """
    np.random.seed(seed)

    # Filter by difficulty if specified
    data = df[df["level"] == difficulty_level] if difficulty_level else df

    # Sample from each group
    adhd_count = sum(data["is_adhd"])
    control_count = sum(~data["is_adhd"])

    adhd_trials = data[data["is_adhd"]].sample(n=min(n_each, adhd_count))
    control_trials = data[~data["is_adhd"]].sample(n=min(n_each, control_count))

    fig, axes = plt.subplots(2, n_each, figsize=(8 * n_each, 10), dpi=100)

    # Plot ADHD trials (top row)
    for idx, (_, trial) in enumerate(adhd_trials.iterrows()):
        ax = axes[0, idx] if n_each > 1 else axes[0]
        plot_trial_pattern(trial, ax=ax, show_clicks=True)
        if idx == 0:
            ax.text(
                -0.1,
                0.5,
                "ADHD",
                transform=ax.transAxes,
                fontsize=16,
                fontweight="bold",
                rotation=90,
                va="center",
                ha="right",
            )

    # Plot Control trials (bottom row)
    for idx, (_, trial) in enumerate(control_trials.iterrows()):
        ax = axes[1, idx] if n_each > 1 else axes[1]
        plot_trial_pattern(trial, ax=ax, show_clicks=True)
        if idx == 0:
            ax.text(
                -0.1,
                0.5,
                "Control",
                transform=ax.transAxes,
                fontsize=16,
                fontweight="bold",
                rotation=90,
                va="center",
                ha="right",
            )

    title = f"ADHD vs Control Comparison"
    if difficulty_level:
        title += f" (Difficulty Level: {difficulty_level})"
    fig.suptitle(title, fontsize=16, fontweight="bold", y=0.995)

    plt.tight_layout()
    return fig
