# Hướng Dẫn Truy Cập Dữ Liệu: OASIS-3 & NSRR MESA

## 📋 Tổng Quan

| Dataset | Registration | Approval Time | Data Available |
|---------|--------------|---------------|----------------|
| **OASIS-3** | NITRC account + Research Statement | 3-5 ngày | MRI + PET (1,378 participants) |
| **NSRR MESA** | NSRR account + Data Request | ~2 tuần | PSG + Actigraphy (2,237 participants) |

---

## 🧠 OASIS-3: Brain MRI + PET Dataset

### Dataset Contents
- **Participants:** 1,378 (755 cognitively normal, 622 with cognitive decline)
- **Age Range:** 42-95 years
- **MRI Sessions:** 2,842 (T1w, T2w, FLAIR, ASL, SWI, resting-state BOLD, DTI)
- **PET Sessions:** 2,157 (PIB amyloid, AV45 Florbetapir, FDG)
- **Tau PET:** 451 sessions (AV1451 Flortaucipir)
- **Processed Data:** FreeSurfer volumetric segmentations

### Bước 1: Tạo Tài Khoản NITRC

1. Truy cập: https://www.nitrc.org/account/register.php
2. **BẮT BUỘC:** Sử dụng email **institutional** (không chấp nhận Gmail, Yahoo)
3. Điền thông tin:
   - Username
   - Email (institutional)
   - Password
   - Institution name

### Bước 2: Nộp Đơn Xin Truy Cập OASIS

1. Truy cập: https://sites.wustl.edu/oasisbrains/home/access/
2. Điền form với các thông tin:

   **Thông tin cơ bản:**
   - Name
   - Institutional Email
   - Institution/Organization

   **Research Statement (Chi tiết):**
   - **Aims:** Mục tiêu nghiên cứu
   - **Proposed Methods:** Phương pháp dự kiến
   - **Variables of Interest:** Các biến quan tâm

   **Ví dụ Research Statement cho TTE2026:**
   ```
   Aims: To develop a brain age prediction model using multimodal neuroimaging 
   data (MRI, PET) and investigate associations between sleep patterns and 
   brain aging biomarkers.

   Proposed Methods: We will use deep learning approaches (convolutional 
   neural networks) to predict brain age from T1-weighted MRI scans. 
   The brain age gap (predicted - chronological age) will be calculated 
   as a marker of brain aging acceleration.

   Variables of Interest: T1-weighted MRI scans, FreeSurfer volumetric 
   measures (hippocampal volume, cortical thickness), cognitive assessments 
   (CDR, MMSE), demographics (age, sex, education).
   ```

3. **Chọn datasets:** Tick OASIS-3
4. **Đồng ý Data Use Agreement:** 10 điều khoản
5. Submit và chờ email approval (3-5 business days)

### Bước 3: Download Sau Khi Approved

1. Nhận email invitation từ OASIS Admin
2. Truy cập NITRC-IR: https://www.nitrc.org/ir
3. Download bằng XNAT hoặc scripts: https://github.com/NrgXnat/oasis-scripts

### ⚠️ Lưu Ý Quan Trọng

- **Country Restrictions:** NIH policies hạn chế access từ một số quốc gia (China, Russia, Iran, North Korea, Cuba, Venezuela)
- **Vietnam:** Cần verify - có thể cần collaboration với US/EU institution
- **Institutional Email:** Gmail/Yahoo KHÔNG được chấp nhận

---

## 😴 NSRR MESA Sleep Dataset

### Dataset Contents
- **Participants:** 2,237 (ages 45-84, multi-ethnic)
- **Polysomnography:** Full overnight unattended PSG
- **Actigraphy:** 7-day wrist-worn data (raw + scored)
- **Sleep Questionnaires:** Detailed sleep habits
- **Covariates:** Demographics, cardiovascular factors

### Bước 1: Tạo Tài Khoản NSRR

1. Truy cập: https://sleepdata.org/join
2. Điền:
   - Username
   - Email (any email OK)
   - Password
   - ORCID iD (optional nhưng recommended)

### Bước 2: Request Data Access

1. Đăng nhập vào NSRR
2. Truy cập MESA dataset: https://sleepdata.org/datasets/mesa
3. Click "Request Data Access"
4. Complete multi-step form:
   - Research purpose
   - Data use statement
   - IRB approval/exemption (nếu có)

### Bước 3: Chờ Approval

- Review time: **~2 tuần**
- NSRR team sẽ review và gửi email confirmation

### Bước 4: Download Data

**Option A: Web Interface**
- Login và browse files trực tiếp

**Option B: NSRR Ruby Gem (Recommended cho large downloads)**
```bash
# Install Ruby gem
gem install nsrr

# Generate API token từ profile page
# https://sleepdata.org/settings

# Download toàn bộ MESA
nsrr download mesa

# Download folder cụ thể
nsrr download mesa/polysomnography/edfs
nsrr download mesa/actigraphy
```

### MESA Data Structure
```
mesa/
├── polysomnography/
│   ├── edfs/          # Raw PSG signals (.edf files)
│   └── annotations/   # Sleep staging, events
├── actigraphy/
│   ├── raw/           # Raw accelerometer data
│   └── scored/        # Processed sleep/wake data
├── datasets/          # CSV covariate files
└── documentation/     # Data dictionaries
```

---

## 📊 Sample Data Không Cần Đăng Ký

### PhysioNet (OPEN ACCESS NOW)

1. **Sleep-EDF Database**
   - URL: https://physionet.org/content/sleep-edfx/
   - 197 PSG recordings
   - Great for algorithm development

2. **SHHS PSG Subset**
   - URL: https://physionet.org/content/shhpsgdb/
   - Limited subset của Sleep Heart Health Study
   - Có thể download ngay

### Kaggle Datasets

1. **OASIS Alzheimer's Detection** (Preprocessed)
   - URL: https://www.kaggle.com/datasets/ninadaithal/oasis-alzheimers-detection
   - 80,000 brain MRI images (processed từ OASIS)
   - Format: JPG images for deep learning

---

## 📅 Timeline Đề Xuất

### Tuần 1
- [ ] Đăng ký NITRC account (institutional email)
- [ ] Submit OASIS-3 application
- [ ] Đăng ký NSRR account
- [ ] Submit MESA data request
- [ ] Download PhysioNet Sleep-EDF (ngay)

### Tuần 2-3
- [ ] Nhận OASIS-3 approval
- [ ] Download OASIS-3 MRI data
- [ ] Bắt đầu train brain age model

### Tuần 3-4
- [ ] Nhận NSRR MESA approval
- [ ] Download MESA PSG + actigraphy
- [ ] Develop sleep feature extraction pipeline

---

## 🔧 Công Cụ Hỗ Trợ

### Brain Age Model Training
```python
# DeepBrainNet (pre-trained)
pip install deepbrainage

# FreeSurfer (volumetric analysis)
# Download: https://surfer.nmr.mgh.harvard.edu/fswiki/DownloadAndInstall
```

### Sleep Analysis
```python
# MNE-Python (EEG/PSG analysis)
pip install mne

# YASA (Yet Another Sleep Architecture)
pip install yasa

# pyActigraphy (actigraphy analysis)
pip install pyActigraphy
```

---

## 📧 Contact Information

### OASIS Support
- Email: oasis@wustl.edu
- FAQ: https://sites.wustl.edu/oasisbrains/home/oasis-resources-and-faq/

### NSRR Support
- Forum: https://sleepdata.org/forum
- Email: support@sleepdata.org

---

## ✅ Checklist Trước Khi Apply

### OASIS-3
- [ ] Có institutional email address
- [ ] Đã tạo NITRC account
- [ ] Đã chuẩn bị Research Statement (Aims, Methods, Variables)
- [ ] Confirm country không bị restricted

### NSRR MESA
- [ ] Đã tạo NSRR account
- [ ] Đã chuẩn bị research purpose statement
- [ ] IRB approval/exemption (if applicable)
- [ ] Ruby installed (for gem download tool)
