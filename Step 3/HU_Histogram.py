import os
import nibabel as nib
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd 

##DICOM 전체를 NifTI로 돌린 폴더를 입력
def load_dcmnifti(CT_path):
    try:
        dcmdata = nib.load(CT_path).get_fdata()
        return dcmdata
    except Exception as e:
        print(f'CT nii 파일 로딩 안 됨...: {e}')
        return None
def load_masknifti(mask_path):
    try:
        niftidata = nib.load(mask_path).get_fdata()
        return niftidata
    except Exception as e:
        print(f"마스크 로딩 안 됨...: {e}")
        return None

def main():
    print('nii Version')
    CT_path = input('CT의 nii 파일 경로를 입력해 보아요: ')
    mask_path = input('mask nii 파일 경로를 입력해 보아요: ')
    output_path = input('출력 경로를 입력해 보아요: ')

    if not os.path.exists(CT_path):
        print("CT nii 폴더 경로가 존재하지 않아요...")
        return
    if not os.path.exists(mask_path):
        print("마스크 파일 경로가 존재하지 않아요...")
        return
    if not os.path.exists(output_path):
        print("경로가 존재하지 않아요...")
        return
    if os.path.isdir(output_path):
        output_path = os.path.join(output_path, 'histo_mask.csv')

        ct_data = load_dcmnifti(CT_path)
        mask_data = load_masknifti(mask_path)

    if ct_data is None or mask_data is None:
        return

    if ct_data.shape != mask_data.shape:
        print(f"CT({ct_data.shape})와 마스크({mask_data.shape})의 shape이 달라요.")
        return

    ##masked_voxels는 전체 DICOM NifTi 파일에 대해 NifTI Mask와 같은 값만 추출
    masked_voxels = ct_data[mask_data>0]    

    if masked_voxels.size == 0:
        print('마스크 영역이 없습니다...')
        return 

    ##OncoSoft 버전에서 주로 나오던 bin 영역대로 설정 
    bins = np.arange(-184, 698, 1)
    hist_counts, hist_bins = np.histogram(masked_voxels, bins=bins)
    hist_portions = hist_counts/hist_counts.sum()
    hist_centers = (hist_bins[:-1]+hist_bins[1:])/2
    df = pd.DataFrame({
        'Bin Center': hist_centers.astype(int), 'Portions': hist_portions
        })
    df.to_csv(output_path, index=False)

    plt.hist(masked_voxels.flatten(), bins=bins, color='gray')
    plt.title("HU Histogram")
    plt.xlabel("Hounsfield Unit (HU)")
    plt.ylabel("Voxel Count")
    plt.show()

if __name__ == "__main__":
    main()
