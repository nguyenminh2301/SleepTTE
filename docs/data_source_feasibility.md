# Data Source Feasibility Analysis: TTE2026_sleep

## Executive Summary

Sau khi nghiên cứu các nguồn dữ liệu công khai, dưới đây là đánh giá chi tiết về tính khả thi của từng dataset cho dự án **Precision Sleep for Brain Aging**.

---

## 🏆 Đánh Giá Tổng Hợp Các Nguồn Dữ Liệu

| Dataset | Sleep Data | Brain Imaging | Cognitive | Sample Size | Accessibility | **Overall Score** |
|---------|------------|---------------|-----------|-------------|---------------|-------------------|
| **UK Biobank** | ✅ Actigraphy (100K+) | ✅ MRI (90K) | ✅ | 500,000 | ⚠️ Application | ⭐⭐⭐⭐⭐ |
| **NSRR (MESA/SHHS)** | ✅ PSG + Actigraphy | ⚠️ Limited | ✅ | 26,000+ | ✅ Free | ⭐⭐⭐⭐ |
| **PREVENT-AD** | ⚠️ Sleep quality | ✅ MRI/PET | ✅ | 400 | ⚠️ Registered | ⭐⭐⭐⭐ |
| **OASIS-3** | ❌ Limited | ✅ MRI/PET | ✅ | 1,378 | ✅ Open | ⭐⭐⭐ |
| **ADNI** | ⚠️ Self-report | ✅ MRI/PET | ✅ | 2,000+ | ⚠️ Application | ⭐⭐⭐ |
| **Whitehall II** | ⚠️ Self-report + subset | ✅ MRI substudy | ✅ | 10,308 | ⚠️ DPUK | ⭐⭐⭐ |
| **HCP** | ❌ PSQI only | ✅ 3T/7T MRI | ⚠️ Limited | 1,200 | ✅ Open | ⭐⭐ |

---

## 📊 Phân Tích Chi Tiết Từng Nguồn

### 1. UK Biobank ⭐⭐⭐⭐⭐ (HIGHLY RECOMMENDED)

**Ưu điểm:**
- **Actigraphy**: 100,000+ participants với 7-day wrist-worn accelerometer
- **Brain MRI**: 90,000 participants (mục tiêu 100,000)
- **Large sample size**: 500,000 tổng thể
- **Sleep features derived**: Sleep duration, efficiency, fragmentation, timing
- **Genetic data**: GWAS available cho sleep-brain associations

**Hạn chế:**
- Application process: 2-4 tuần
- Access fee: ~£2,000-5,000
- Data size: Terabytes, cần infrastructure

**Khả thi cho TTE2026:**
- ✅ Sleep-to-Brain Aging Signature: EXCELLENT
- ✅ Observational associations: EXCELLENT  
- ⚠️ Target trial emulation: LIMITED (no intervention data)

**Link:** https://www.ukbiobank.ac.uk/

---

### 2. National Sleep Research Resource (NSRR) ⭐⭐⭐⭐

**Datasets khả dụng:**

| Study | N | Sleep Data | Brain | Cognition |
|-------|---|------------|-------|-----------|
| MESA Sleep | 2,237 | PSG + 7-day actigraphy | ⚠️ Cardiac MRI | ✅ |
| SHHS | 5,800+ | Full PSG | ❌ | ⚠️ |
| MrOS Sleep | 3,000+ | PSG + actigraphy | ❌ | ✅ Dementia outcome |
| SOF-Sleep | 400+ | PSG + actigraphy | ❌ | ✅ Dementia outcome |
| CHAT | 400+ | PSG | ❌ | ✅ Pediatric |

**Ưu điểm:**
- **FREE ACCESS** sau khi đăng ký
- Raw PSG signals + sleep staging
- Well-documented
- API available for download

**Hạn chế:**
- **Không có brain MRI** trong hầu hết studies
- Cần merge với brain imaging cohort khác

**Khả thi cho TTE2026:**
- ✅ Sleep feature development: EXCELLENT
- ⚠️ Sleep-brain associations: LIMITED (no brain imaging)
- ✅ Cognitive outcomes: GOOD

**Link:** https://sleepdata.org/

---

### 3. PREVENT-AD ⭐⭐⭐⭐

**Ưu điểm:**
- **AD biomarkers**: MRI + PET (amyloid, tau) + plasma
- **Longitudinal**: Multiple timepoints
- **High-risk cohort**: Family history of AD
- **Open + Registered tiers**

**Hạn chế:**
- **Sleep data limited**: Có "sleep quality" questionnaire, KHÔNG có actigraphy
- Sample size nhỏ (~400)
- Cần verify registered access

**Khả thi cho TTE2026:**
- ⚠️ Sleep-to-Brain signatures: LIMITED (no objective sleep)
- ✅ Brain aging biomarkers: EXCELLENT
- ❌ Target trial emulation: NOT FEASIBLE (no intervention)

**Link:** https://portal.conp.ca/dataset?id=projects/preventad-registered

---

### 4. OASIS-3 ⭐⭐⭐

**Ưu điểm:**
- **OPEN ACCESS** - dễ dàng download
- 1,378 participants với longitudinal MRI + PET
- FreeSurfer processed data available
- Good for brain aging models

**Hạn chế:**
- **KHÔNG có sleep data**
- Chỉ dùng được cho brain age modeling, KHÔNG dùng được cho sleep associations

**Khả thi cho TTE2026:**
- ✅ Brain age model training: EXCELLENT
- ❌ Sleep associations: NOT POSSIBLE

**Link:** https://www.oasis-brains.org/

---

### 5. ADNI ⭐⭐⭐

**Ưu điểm:**
- Gold standard cho AD research
- Rich neuroimaging (MRI, PET)
- Longitudinal cognitive data
- Sleep disorder history trong medical records

**Hạn chế:**
- **Không có objective sleep data** (PSG/actigraphy)
- Self-report sleep only
- Complex application process

**Link:** https://adni.loni.usc.edu/

---

### 6. Whitehall II ⭐⭐⭐

**Ưu điểm:**
- Longitudinal (30+ years)
- MRI substudy với brain imaging
- Sleep duration trajectories
- Cognitive aging outcomes

**Hạn chế:**
- Actigraphy chỉ có cho subset
- Access qua DPUK (process phức tạp)

**Link:** https://www.dpuk.org/

---

## 🎯 Chiến Lược Đề Xuất

### Option A: UK Biobank Focus (Best for Full Project)

```
Timeline: 3-6 months for access
Sleep: Actigraphy (N=100,000+)
Brain: MRI (N=90,000)
Overlap: ~30,000-50,000 participants có cả hai
```

**Workflow:**
1. Submit UK Biobank application
2. Develop brain age models
3. Extract sleep signatures from actigraphy
4. Build sleep-brain associations
5. Platform development với UK Biobank-derived models

### Option B: Multi-Source Approach (Immediate Start)

```
OASIS-3: Brain age model training (OPEN NOW)
NSRR/MESA: Sleep feature development (FREE NOW)
PREVENT-AD: AD biomarker validation (REGISTERED)
```

**Workflow:**
1. Download OASIS-3 NOW → train brain age models
2. Download NSRR/MESA NOW → develop sleep algorithms
3. Apply for PREVENT-AD registered access
4. Merge insights from multiple sources

### Option C: Synthetic + Real Hybrid

```
Start: Synthetic data (DONE - sample data created)
Phase 1: OASIS-3 for brain age
Phase 2: NSRR for sleep features
Phase 3: UK Biobank for full integration
```

---

## 📥 Datasets Available for Immediate Download

### 1. OASIS-3 (Brain MRI + PET)
- **Status:** OPEN ACCESS
- **Download:** https://www.oasis-brains.org/
- **Use case:** Brain age model development

### 2. NSRR MESA Sleep
- **Status:** FREE after registration
- **Download:** https://sleepdata.org/datasets/mesa
- **Use case:** Sleep feature algorithms, PSG + actigraphy

### 3. NSRR SHHS 
- **Status:** FREE after registration
- **Download:** https://sleepdata.org/datasets/shhs
- **Use case:** Sleep-cardiovascular associations

### 4. PhysioNet Sleep Datasets
- **Status:** OPEN ACCESS
- **Multiple PSG datasets available**
- **Use case:** Algorithm validation

---

## 💡 Khuyến Nghị Tiếp Theo

1. **Ngay lập tức:** Download OASIS-3 và NSRR MESA để bắt đầu phát triển
2. **Tuần 1-2:** Submit UK Biobank application
3. **Tuần 2-4:** Xây dựng brain age model với OASIS-3
4. **Tuần 4-8:** Phát triển sleep algorithms với NSRR
5. **Tháng 2-3:** Nhận UK Biobank access, integrate full pipeline

---

## Kết Luận Khả Thi

| Component | Khả thi? | Best Data Source |
|-----------|----------|------------------|
| Sleep Feature Extraction | ✅ Rất cao | NSRR/UK Biobank |
| Brain Age Prediction | ✅ Rất cao | OASIS-3/UK Biobank |
| Sleep-Brain Association | ✅ Cao | UK Biobank |
| Target Trial Emulation | ⚠️ Trung bình | Cần clinical intervention data |
| Digital Platform | ✅ Rất cao | Model-agnostic |

**Overall Feasibility: 75-85%** với điều kiện sử dụng UK Biobank hoặc multi-source approach.
