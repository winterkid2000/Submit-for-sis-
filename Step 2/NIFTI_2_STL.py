import os
import nibabel as nib
import numpy as np
from skimage import measure
from stl import mesh
from tqdm import tqdm

def nifti_to_stl(nifti_path: str, stl_path: str, threshold: float = 0):
    ##nibabel로 NIfTI 마스크가 갖고 있는 데이터부터 추출
    try:
        img = nib.load(nifti_path)
        data = img.get_fdata()
        affine = img.affine

        ##마스크 영역의 임계값을 정해서 어떤 느낌으로 갈지 결정 
        binary_mask = data > threshold
        if not np.any(binary_mask):
            raise ValueError("Threshold보다 큰 값이 없는뎅... 마스크가 비어 있는 거 같애")
            
        ##Marching Cubes 알고리즘 적용
        verts, faces, _, _ = measure.marching_cubes(binary_mask.astype(np.float32), level=0)

        verts_homogeneous = np.c_[verts, np.ones(len(verts))]
        verts_transformed = np.dot(affine, verts_homogeneous.T).T[:, :3]

        stl_mesh = mesh.Mesh(np.zeros(faces.shape[0], dtype=mesh.Mesh.dtype))
        for i, f in enumerate(faces):
            for j in range(3):
                stl_mesh.vectors[i][j] = verts_transformed[f[j], :]

        os.makedirs(os.path.dirname(stl_path), exist_ok=True)
        stl_mesh.save(stl_path)
        return True

    except Exception as e:
        print(f"Blast {nifti_path} 변환 오류: {e}")
        return False
        
##위 nifti_to_stl 함수가 돌아가기 위해 어떤 방식일지 정의 
def convert_all_nii_to_stl_simple(nii_base_path: str, stl_output_path: str, threshold: float = 0):
    failed = []

    for patient_folder in tqdm(os.listdir(nii_base_path), desc="환자별 STL 변환 中"):
        patient_path = os.path.join(nii_base_path, patient_folder)
        if not os.path.isdir(patient_path):
            continue

        for fname in os.listdir(patient_path):
            if not fname.lower().endswith(".nii"):
                continue

            nii_path = os.path.join(patient_path, fname)
            stl_dir = os.path.join(stl_output_path, patient_folder)
            stl_filename = fname.replace(".nii", ".stl")
            stl_path = os.path.join(stl_dir, stl_filename)

            success = nifti_to_stl(nii_path, stl_path, threshold)
            if success:
                print(f"만세 {stl_path}")
            else:
                failed.append(nii_path)

    if failed:
        print("\n댕청해서 미안해...:")
        for f in failed:
            print(" -", f)
    else:
        print("\n모두 변환했어양")

if __name__ == "__main__":
    nii_base = input("NIfTI 시리즈가 있는 폴더를 입력해요: ").strip()
    stl_base = input("어디에 두고 싶나요: ").strip()
    convert_all_nii_to_stl_simple(nii_base, stl_base)

