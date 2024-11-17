<p align="center"><img src="static/img/logo_white.png" alt="NeuroKnights Logo" width="200"/></p>

<h1 align="center">NeuroKnights Gambit: <br/> Revolutionizing Chess Through Mind Control</h1>

Discover a new era of accessible neuroscience with **NeuroKnights Gambit** — a groundbreaking project that brings mind-controlled chess to life. Designed for reproducibility, our innovative system empowers even beginners in neurotechnology to control a Unity-powered chess game using only their focus on visual stimuli. By harnessing the power of *Steady-State Visual Evoked Potential* (SSVEP) through a *Brain-Computer Interface* (BCI), players can control gameplay seamlessly without traditional input devices.

[Check out on Devpost how our project performed in natHacks2024!](https://devpost.com/software/neuroknights-gambit)

## How does it work?

### 1. Brain Signal Acquisition
The project begins with acquiring brain signals using the NeuroPawn EEG Headset, a device equipped with 8 electrode channels strategically placed to access the occipital lobe. This area of the brain is responsible for visual processing, making it ideal for detecting Steady-State Visual Evoked Potentials (SSVEPs). The headset streams real-time EEG data using BrainFlow, a versatile library for interfacing with EEG hardware. This data includes raw brain activity that reflects the user’s focus on specific flickering stimuli presented during gameplay. The robust design of the NeuroPawn headset ensures high-quality signal acquisition, critical for accurate SSVEP classification. Its integration with BrainFlow allows seamless data streaming and board configuration, making it a foundational component of the project.

---
***Please note that the following information is simply for more insight into our project.***

**Credit** Built upon https://github.com/eliasakesson/Unity-Chess
