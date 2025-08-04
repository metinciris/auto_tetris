# auto_tetris
# Tetris Screen Saver

A modern, visually appealing Tetris game implemented as a screen saver using Python and Tkinter. This screen saver automatically activates and runs a fully functional Tetris game with an AI-driven autoplay feature. It is designed to stay unobtrusive by running in the background, ensuring it does not interfere with foreground applications like YouTube videos.

## Features

- **Classic Tetris Gameplay**: Implements the traditional Tetris mechanics with seven unique block shapes (I, J, L, O, S, T, Z) and standard scoring for cleared lines.
- **AI Autoplay**: Includes an intelligent `AutoPlayer` that uses a heuristic-based algorithm to make optimal moves, considering factors like smoothness, total height, holes, and completed lines.
- **High Score System**: Tracks and displays daily and all-time high scores, stored persistently in a `high_scores.json` file.
- **Fullscreen Display**: Runs in fullscreen mode with a dark theme, centered game board, and clear visual styling for blocks and UI elements.
- **Non-Intrusive Behavior**: Designed to run as a screen saver, staying in the background without interrupting foreground applications, such as YouTube videos playing in a browser.
- **Interactive Controls**: Supports manual control with keyboard inputs for testing or manual play, alongside the autoplay mode.
- **Responsive Exit**: Exits the screen saver on any key press or mouse movement for a seamless user experience.

## Controls

- **Spacebar**: Drop the current block instantly.
- **A**: Move the block left.
- **S**: Move the block right.
- **K**: Rotate the block counterclockwise.
- **L**: Rotate the block clockwise.
- **Y**: Toggle autoplay on/off.
- **R**: Restart the game.
- **Q**: Quit the screen saver.
- **Any Key/Mouse Movement**: Exit the screen saver.

## Installation

1. **Prerequisites**:
   - Python 3.x
   - Tkinter (usually included with Python; install `python3-tk` on Linux if needed)

2. **Clone the Repository**:
   ```bash
   git clone https://github.com/yourusername/tetris-screen-saver.git
   cd tetris-screen-saver
   ```

3. **Run the Game**:
   ```bash
   python tetris.py
   ```

   Replace `tetris.py` with the actual filename of the script.

## File Structure

- `tetris.py`: Main script containing the Tetris game logic, including model, view, controller, and autoplay components.
- `high_scores.json`: Automatically generated file to store daily and all-time high scores.

## Technical Details

- **Language**: Python 3
- **Library**: Tkinter for GUI rendering
- **Architecture**:
  - **Model**: Manages game state, including block movement, rotation, collision detection, and scoring.
  - **View**: Handles rendering of the game board, falling blocks, next block preview, score, and high scores.
  - **Controller**: Coordinates user input, game updates, and screen saver functionality.
  - **AutoPlayer**: Implements an AI that evaluates board states to make optimal moves based on weighted heuristics.
- **Settings**:
  - `GRID_SIZE = 30`: Size of each block tile in pixels.
  - `MAXROW = 20`, `MAXCOL = 10`: Game board dimensions.
  - `TOP_OFFSET = GRID_SIZE * 6`: Vertical offset for the game board to ensure proper positioning.
- **High Score Persistence**: Scores are saved in `high_scores.json` with timestamps, maintaining up to 25 daily and all-time entries.

## Notes

- The screen saver is designed to run unobtrusively, staying behind active windows (e.g., YouTube videos) without stealing focus.
- The autoplay feature uses a sophisticated heuristic algorithm, tunable via weights in the `AutoPlayer` class for different gameplay strategies.
- The game board is centered with a dark gray background and a subtle border for better visibility.
- High score displays (daily and all-time) are shown without borders for a clean look, positioned on the left and right sides of the screen.

## License

This project is licensed under the MIT License. See the `LICENSE` file for details.

## Contributing

Contributions are welcome! Please submit a pull request or open an issue for bug reports, feature requests, or improvements.

---

*This README is tailored for a GitHub repository hosting the Tetris screen saver. Replace `yourusername` in the clone command with your actual GitHub username. If you need a specific license file or additional sections (e.g., screenshots, build instructions), let me know!*
