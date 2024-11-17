<p align="center"><img src="static/img/logo_white.png" alt="NeuroKnights Logo" width="200"/></p>

<h1 align="center">NeuroKnights Gambit: <br/> Revolutionizing Chess Through Mind Control</h1>

Discover a new era of accessible neuroscience with **NeuroKnights Gambit** — a groundbreaking project that brings mind-controlled chess to life. Designed for reproducibility, our innovative system empowers even beginners in neurotechnology to control a Unity-powered chess game using only their focus on visual stimuli. By harnessing the power of *Steady-State Visual Evoked Potential* (SSVEP) through a *Brain-Computer Interface* (BCI), players can control gameplay seamlessly without traditional input devices.

<a href="https://devpost.com/software/neuroknights-gambit" target="_blank">Check out our project on Devpost!</a>

## How does it work?

The system utilizes the NeuroPawn EEG Headset, which captures real-time brain signals from 8 occipital-lobe electrode channels via BrainFlow. Preprocessing is handled by the `DataProcessor` class, which applies detrending, filtering, and *Common Average Referencing* (CAR) to clean the signals. The `FoCAA-KNN` framework performs SSVEP classification using *Canonical Correlation Analysis* (CCA), detecting the frequency a user focuses on.

By displaying flickering visual cues on the Unity interface that correspond to chess moves, NeuroKnights Gambit translates your focused attention into game actions. Whether you're selecting a piece, choosing where to move, or confirming a decision, your gaze becomes your game controller, making interaction possible without traditional inputs.

All in all, to ensure a seamless experience, the project incorporates robust data logging for EEG signals and classification results, an intuitive User Interface built using Qt5 and our custom Unity chess game.  We hope that projects like this, where all hardware used adds up to less than $200 will serve to lower the barrier to start exploring neurotechnology. **In fact, working on this project has already helped the five of us—first-year students with no prior experience—delve into the field, and we hope to inspire others to do the same.**

**NeuroKnights Gambit** revolutionizes the way you play chess, offering an immersive, hands-free gaming adventure. Experience the future of interactive entertainment, where neurotechnology meets accessibility, and your mind is the ultimate game controller.

---
***Please note that the following information is simply for more insight into our project.***

**Credit** Built upon https://github.com/eliasakesson/Unity-Chess
