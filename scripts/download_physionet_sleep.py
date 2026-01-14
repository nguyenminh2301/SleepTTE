"""
Download PhysioNet Sleep-EDF Sample Data
This dataset is OPEN ACCESS and can be downloaded immediately without registration
Use for algorithm development and testing before OASIS-3/NSRR access is approved
"""

import os
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Create data directory
DATA_DIR = Path("data/external/sleep_edf")
DATA_DIR.mkdir(parents=True, exist_ok=True)


def download_with_mne():
    """
    Download Sleep-EDF data using MNE-Python's built-in fetcher
    This automatically downloads from PhysioNet
    """
    try:
        import mne
        from mne.datasets.sleep_physionet.age import fetch_data
        
        logger.info("="*60)
        logger.info("Downloading PhysioNet Sleep-EDF Data via MNE")
        logger.info("="*60)
        
        # Download data for 2 subjects as sample
        # Full dataset has ~20 subjects with 2 nights each
        subjects = [0, 1]  # Start with first 2 subjects
        recording = [1, 2]  # Night 1 and Night 2
        
        logger.info(f"Downloading {len(subjects)} subjects, {len(recording)} nights each...")
        
        for subj in subjects:
            for rec in recording:
                try:
                    # MNE's fetch_data automatically handles the path
                    paths = fetch_data(
                        subjects=[subj], 
                        recording=[rec]
                    )
                    logger.info(f"✓ Downloaded Subject {subj}, Night {rec}")
                    logger.info(f"  Files: {paths}")
                except Exception as e:
                    logger.warning(f"⚠ Could not download Subject {subj}, Night {rec}: {e}")
        
        logger.info("\nDownload complete!")
        
        # Get the MNE data path where files are stored
        mne_data_path = mne.datasets.sleep_physionet.age.data_path()
        logger.info(f"Data saved to: {mne_data_path}")
        
        return True
        
    except ImportError:
        logger.error("MNE-Python not installed. Install with: pip install mne")
        return False


def download_with_requests():
    """
    Alternative: Download directly from PhysioNet using requests
    """
    import requests
    
    logger.info("="*60)
    logger.info("Downloading Sleep-EDF Data directly from PhysioNet")
    logger.info("="*60)
    
    base_url = "https://physionet.org/files/sleep-edfx/1.0.0/sleep-cassette"
    
    # Sample files to download
    sample_files = [
        "SC4001E0-PSG.edf",
        "SC4001EC-Hypnogram.edf",
        "SC4002E0-PSG.edf", 
        "SC4002EC-Hypnogram.edf"
    ]
    
    for filename in sample_files:
        url = f"{base_url}/{filename}"
        output_path = DATA_DIR / filename
        
        if output_path.exists():
            logger.info(f"✓ Already exists: {filename}")
            continue
            
        logger.info(f"Downloading: {filename}...")
        
        try:
            response = requests.get(url, stream=True)
            response.raise_for_status()
            
            with open(output_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            logger.info(f"✓ Downloaded: {filename}")
            
        except Exception as e:
            logger.error(f"✗ Failed to download {filename}: {e}")
    
    logger.info("\nDownload complete!")
    logger.info(f"Data saved to: {DATA_DIR}")


def analyze_sample_data():
    """
    Quick analysis of downloaded Sleep-EDF data
    """
    try:
        import mne
        
        logger.info("\n" + "="*60)
        logger.info("Analyzing Sample Sleep-EDF Data")
        logger.info("="*60)
        
        # Find PSG files
        psg_files = list(DATA_DIR.rglob("*PSG.edf"))
        logger.info(f"Found {len(psg_files)} PSG files")
        
        if not psg_files:
            logger.warning("No PSG files found. Run download first.")
            return
        
        # Load first PSG file
        psg_file = psg_files[0]
        logger.info(f"\nLoading: {psg_file.name}")
        
        raw = mne.io.read_raw_edf(str(psg_file), preload=True, verbose=False)
        
        # Print info
        logger.info(f"\nRecording Info:")
        logger.info(f"  Duration: {raw.times[-1]/3600:.2f} hours")
        logger.info(f"  Channels: {raw.ch_names}")
        logger.info(f"  Sampling rate: {raw.info['sfreq']} Hz")
        
        # Find corresponding hypnogram
        hypno_file = psg_file.parent / psg_file.name.replace("PSG", "Hypnogram")
        
        if hypno_file.exists():
            annotations = mne.read_annotations(str(hypno_file))
            logger.info(f"\nSleep Stages Found:")
            
            # Count sleep stages
            stage_counts = {}
            for desc in annotations.description:
                stage_counts[desc] = stage_counts.get(desc, 0) + 1
            
            for stage, count in sorted(stage_counts.items()):
                logger.info(f"  {stage}: {count} epochs")
        
        logger.info("\n✓ Sample data analysis complete!")
        
    except ImportError:
        logger.error("MNE-Python not installed. Install with: pip install mne")
    except Exception as e:
        logger.error(f"Error analyzing data: {e}")


def main():
    """Main download workflow"""
    logger.info("="*60)
    logger.info("PhysioNet Sleep-EDF Sample Data Downloader")
    logger.info("="*60)
    logger.info("\nThis dataset is OPEN ACCESS - no registration required!")
    logger.info("Use for algorithm development before OASIS-3/NSRR approval\n")
    
    # Check if MNE is available
    try:
        import mne
        logger.info("✓ MNE-Python detected. Using MNE downloader.")
        success = download_with_mne()
    except ImportError:
        logger.warning("MNE-Python not found. Trying direct download...")
        try:
            download_with_requests()
        except ImportError:
            logger.error("Please install requests: pip install requests")
            return
    
    # Analyze if download succeeded
    analyze_sample_data()
    
    logger.info("\n" + "="*60)
    logger.info("NEXT STEPS")
    logger.info("="*60)
    logger.info("""
    1. Use this Sleep-EDF data to develop sleep staging algorithms
    2. Test actigraphy feature extraction code
    3. While waiting for OASIS-3/NSRR approval:
       - Train preliminary models
       - Validate pipeline components
       - Develop visualization tools
    
    Useful MNE tutorials:
    - Sleep staging: https://mne.tools/stable/auto_tutorials/clinical/60_sleep.html
    - EEG analysis: https://mne.tools/stable/auto_tutorials/index.html
    """)


if __name__ == "__main__":
    main()
