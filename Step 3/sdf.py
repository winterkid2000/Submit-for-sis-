import os
import nibabel as nib
import numpy as np
import pandas as pd
from scipy.stats import skew, kurtosis

def load_nifti(path):
    return nib.load(path)

def extract_hu_features(ct_path, mask_path):
    try:
        ct_img = load_nifti(ct_path)
        mask_img = load_nifti(mask_path)

        ct = ct_img.get_fdata()
        mask = mask_img.get_fdata()

        hu_values = ct[mask > 0]

        if len(hu_values) == 0:
            raise ValueError("❌ 마스크 내부에 해당하는 CT 값이 없습니다.")

        voxel_volume = np.prod(ct_img.header.get_zooms())

        features = {
            "Integral_Total_HU": np.sum(hu_values)*0.001,
            "Kurtosis": kurtosis(hu_values),
            "Max_HU": np.max(hu_values),
            "Mean_HU": np.mean(hu_values),
            "Median_HU": np.median(hu_values),
            "Min_HU": np.min(hu_values),
            "Skewness": skew(hu_values),
            "HU_STD": np.std(hu_values),
            "Total_HU": np.sum(hu_values) * voxel_volume,
        }

        return features

    except Exception as e:
        print(f"⚠️ 예외 발생: {e}")
        return {
            "Integral_Total_HU": 0,
            "Kurtosis": 0,
            "Max_HU": 0,
            "Mean_HU": 0,
            "Median_HU": 0,
            "Min_HU": 0,
            "Skewness": 0,
            "HU_STD": 0,
            "Total_HU": 0,
        }

def main():
    print("🔍 단일 CT + 마스크 파일 HU 특징 추출")
    ct_path = input("📄 CT NIfTI 파일 경로 입력: ").strip().strip('"').replace('\\', '/')
    mask_path = input("📄 마스크 NIfTI 파일 경로 입력: ").strip().strip('"').replace('\\', '/')
    output_csv = input("💾 결과 CSV 저장 경로 입력 (예: result.csv): ").strip().strip('"').replace('\\', '/')

    if not os.path.exists(ct_path):
        print(f"❌ CT 파일이 존재하지 않음: {ct_path}")
        return
    if not os.path.exists(mask_path):
        print(f"❌ 마스크 파일이 존재하지 않음: {mask_path}")
        return

    features = extract_hu_features(ct_path, mask_path)
    features["CT_File"] = os.path.basename(ct_path)
    features["Mask_File"] = os.path.basename(mask_path)

    df = pd.DataFrame([features])
    df.to_csv(output_csv, index=False)

    print(f"✅ 저장 완료: {output_csv}")

if __name__ == "__main__":
    main()
