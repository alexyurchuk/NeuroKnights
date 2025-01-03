<p align="center"><img src="static/img/logo_white.png" alt="NeuroKnights Logo" width="200"/></p>

<h1 align="center">NeuroKnights Gambit: <br/> Revolutionizing Chess Through Mind Control</h1>

Discover a new era of accessible neuroscience with **NeuroKnights Gambit** — a groundbreaking project that brings mind-controlled chess to life. Designed for reproducibility, our innovative system empowers even beginners in neurotechnology to control a Unity-powered chess game using only their focus on visual stimuli. By harnessing the power of *Steady-State Visual Evoked Potential* (SSVEP) through a *Brain-Computer Interface* (BCI), players can control gameplay seamlessly without traditional input devices.

[Check out on Devpost how our project performed in natHacks2024!](https://devpost.com/software/neuroknights-gambit)


***Please note that the following information is simply for more insight into our project.***
#### ‎ 
## How does it work?

### **1. Brain Signal Acquisition**
The project begins with acquiring brain signals using the **NeuroPawn EEG Headset**, a device equipped with 8 electrode channels strategically placed to access the occipital lobe. This area of the brain is responsible for visual processing, making it ideal for detecting *Steady-State Visual Evoked Potentials (SSVEPs)*. The headset streams real-time EEG data using **BrainFlow**, a versatile library for interfacing with EEG hardware. This data includes raw brain activity that reflects the user’s focus on specific flickering stimuli presented during gameplay. The robust design of the NeuroPawn headset ensures high-quality signal acquisition, critical for accurate SSVEP classification. Its integration with *BrainFlow* allows seamless data streaming and board configuration, making it a foundational component of the project.

### **2. Preprocessing**
Raw EEG signals are inherently noisy and can be affected by various artifacts, such as eye movements, muscle activity, and environmental interference. To ensure clean and analyzable data, the project employs the **DataProcessor** class for preprocessing. This module applies essential steps like *detrending*, which removes slow drifts in the signal, and *bandpass filtering*, isolating frequencies between 6–40 Hz, where most SSVEP activity lies. Additionally, *bandstop filtering* removes powerline noise at 50 Hz or 60 Hz. A final preprocessing step is *Common Average Referencing (CAR)*, which reduces spatial noise by subtracting the average signal across all channels. These preprocessing techniques ensure that only relevant neural activity reaches the classification stage, improving the system’s accuracy and robustness in real-world conditions.

### **3. Classification**
At the heart of the project is the **FoCAA-KNN framework**, responsible for classifying the user's focused frequency based on the preprocessed EEG signals. It combines *Filter Bank Canonical Correlation Analysis (FBCCA)*, which enhances signal detection by filtering across multiple frequency bands, and *Power Spectral Density (PSD)* for robust feature extraction. FBCCA computes correlations between the EEG data and reference signals to identify the most likely frequency, while PSD analyzes the power distribution in the signal for additional accuracy. These features are fed into a **K-Nearest Neighbors (KNN)** classifier, which is trained to distinguish between stimuli-induced and non-stimuli states. The hybrid pipeline improves classification accuracy and reliability, even in noisy or complex environments, making it a critical component for decoding user intent in real-time.

### **4. Flicker Stimuli Generation**
To elicit SSVEPs, the project uses a **Pygame-based flicker stimulus generator** integrated into Unity. The system displays flickering stimuli at specific frequencies on the chessboard, with each stimulus representing a potential action, such as selecting a piece, moving it, or confirming the choice. These stimuli are designed to maximize user focus and evoke strong SSVEP responses in the occipital lobe. The Unity interface seamlessly combines these visual stimuli with the chess game, creating a dynamic and interactive environment. By mapping specific frequencies to actions, the flicker stimuli act as the primary communication channel between the user’s brain and the game logic.

### **5. Data Logging**
For reproducibility and debugging, the project includes robust data logging capabilities using the **recording module**. It records both preprocessed EEG data and classification results into structured CSV files. Metadata such as timestamps, stimuli states, and detected frequencies are also logged, providing a detailed record of each session. This data is invaluable for offline analysis, allowing researchers to evaluate system performance, improve classification models, and identify areas for optimization. By storing the data in an organized and accessible format, the project ensures transparency and facilitates future development.

### **6. Integration with Unity**
The classified outputs from the SSVEPAnalyzer are integrated into Unity, where they directly trigger game logic. For example, when a user focuses on a flicker stimulus associated with a chess piece, the system detects the corresponding frequency and relays the intent to Unity, which highlights the selected piece. Similar workflows handle move selection and confirmation. Unity acts as the visual and logical engine for the chess game, combining real-time brain inputs with traditional game mechanics to create a cohesive and immersive experience. The modular design of the integration allows for scalability, enabling the addition of new features or applications beyond chess.

### ‎ 
## **Challenges and Innovations**
One of the greatest challenges we faced during this project was achieving accurate classification of the SSVEP stimuli frequency by distinguishing when no stimuli were present. To address this challenge, we developed a hybrid classification pipeline, which combines Filter Bank Canonical Correlation Analysis (FBCCA), a method that enhances signal detection across multiple frequency bands by applying bandpass filters. As well, Power Spectral Density (PSD) was implemented for robust feature extraction. We trained a K-Nearest Neighbors (KNN) classifier for precise and reliable classification of both stimuli-induced and non-stimuli states. This combined approach proved effective in improving accuracy and robustness, particularly in noisy or real-world conditions. Another challenge was integrating the BCI system with Unity, requiring seamless communication between EEG classification outputs and game logic. The project's modular design allowed for efficient troubleshooting and scalability, ensuring a functional and adaptable system. 

#### ‎ 
## **Credit**

### **Research Papers:** 
- [Paper 1](https://www.frontiersin.org/articles/10.3389/fninf.2018.00078/pdf)
- [Paper 2](https://www.researchgate.net/publication/330478575_An_EOGEEG-Based_Hybrid_Brain-Computer_Interface_for_Chess\\)
- [Paper 3](https://pmc.ncbi.nlm.nih.gov/articles/PMC9978185/)
- [Paper 4](https://app.dimensions.ai/details/publication/pub.1155345057?search_mode=content&search_text=motor%20imagery%20AND%20reinforcement%20learning&search_type=kws&search_field=full_search)
- [Paper 5](https://www.frontiersin.org/journals/computational-neuroscience/articles/10.3389/fncom.2022.882290/full)
- [Paper 6](https://www.sciencedirect.com/topics/medicine-and-dentistry/steady-state-visually-evoked-potential#:~:text=Different%20paradigms%20have%20been%20implemented%20so%20far%2C%20such%20as%20P300%20spellers%2C11%20and%20Steady%20State%20Visually%20Evoked%20Potential%20(SSVEP).12%20and%20allow%20the%20user%20to%20drive%20a%20car%2C13%20operate%20robots%2C14%20fly%20a%20helicopter15%20or%20use%20a%20wheelchair.16)
- [Paper 7](https://pure.mpg.de/rest/items/item_3362321_1/component/file_3362322/content)
- [Paper 8](https://www.sciencedirect.com/science/article/pii/S1746809423003907)
- [Paper 9](https://www.sciencedirect.com/science/article/pii/S1746809418301629)
- [Paper 10](https://pure.mpg.de/rest/items/item_3362321_1/component/file_3362322/content)

### **Articles:** 
- [Article 1](https://neuraldatascience.io/7-eeg/erp_artifacts.html#muscle-contractions)
- [Article 2](https://gregorygundersen.com/blog/2018/07/17/cca/)
- [Article 3](https://pmc.ncbi.nlm.nih.gov/articles/PMC9978185/)
- [Article 4](https://datascience.stackexchange.com/questions/17134/recurrent-cnn-model-on-eeg-data)

### **Videos:** 
- [Video 1](https://youtu.be/XQzKG511fNc?si=lfT0tpNW4QEFRY4k)
- [Video 2](https://www.youtube.com/watch?v=metlFBa_NdQ)
- [Video 3](https://www.youtube.com/watch?v=UPf4hU2pAV4)
- [Video 4](https://www.youtube.com/watch?v=8bgvbYVJplM&t=114s)

### **Hardware Used:**
- [NeuroPawn EEG Headset + Knight Board](https://neuropawn.tech/products)
- [Laptop](https://www.dell.com/en-ca/shop/gaming-laptops-pcs-and-accessories/alienware-m15-r7-gaming-laptop/spd/alienware-m15-r7-gaming-laptop)

### **Built upon:**
- [SSVEP & FoCCA-KNN](https://github.com/RezaSaadatyar/SSVEP-based-EEG-signal-processing)
- [Unity Chess](https://github.com/eliasakesson/Unity-Chess)
