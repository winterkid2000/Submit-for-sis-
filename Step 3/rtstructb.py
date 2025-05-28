import os
import nibabel as nib
from rt_utils import RTStructBuilder
import pydicom
from pydicom.tag import Tag
from tqdm import tqdm
import multiprocessing

def is_image_series(dicom_path):
    # 유효한 CT 이미지 시리즈 여부 확인
    try:
        ds = pydicom.dcmread(dicom_path, stop_before_pixels=True, force=True)
        return (
            ds.Modality == 'CT' and 
            ds.SOPClassUID == '1.2.840.10008.5.1.4.1.1.2' and
            hasattr(ds, 'ImagePositionPatient')
        )
    except Exception as e:
        return False

def get_slice_position(dicom_path):
    # DICOM 슬라이스의 Z축 위치 추출
    ds = pydicom.dcmread(dicom_path, stop_before_pixels=True, force=True)
    return float(ds.ImagePositionPatient[2])

def validate_dicom_series(dicom_folder):
    # DICOM 시리즈 유효성 검증 및 정렬된 슬라이스 반환
    slices = []
    for fname in os.listdir(dicom_folder):
        if not fname.lower().endswith('.dcm'):
            continue
            
        file_path = os.path.join(dicom_folder, fname)
        if not is_image_series(file_path):
            continue
            
        try:
            z_pos = get_slice_position(file_path)
            slices.append((z_pos, file_path))
        except Exception as e:
            continue
    
    if not slices:
        raise ValueError("유효한 DICOM 슬라이스가 없습니다")
        
    # Z축 기준 정렬 (내림차순/오름차순 자동 감지)
    slices.sort(key=lambda x: x[0])
    if len(slices) > 1 and slices[0][0] > slices[1][0]:
        slices = sorted(slices, key=lambda x: -x[0])
    
    return slices

def validate_coordinate_system(dicom_slices, nifti_img):
    # DICOM-NIfTI 좌표계 일치 여부 검증
    # DICOM 방향 정보 추출
    sample_ds = pydicom.dcmread(dicom_slices[0][1], force=True)
    dicom_orientation = tuple(map(float, sample_ds.ImageOrientationPatient))
    
    # NIfTI 방향 정보 변환
    nifti_affine = nifti_img.affine
    nifti_orientation = nib.aff2axcodes(nifti_affine)
    
    # 좌표계 일치 여부 검증
    if nifti_orientation not in [('R', 'A', 'S'), ('L', 'P', 'I')]:
        raise ValueError(f"지원되지 않는 NIfTI 방향: {nifti_orientation}")
    
    # 실제 구현 시 DICOM orientation과의 상세 비교 필요

def process_patient(patient_args):
    # 병렬 처리를 위한 환자 단위 처리 함수
    patient_id, ct_base, seg_base, output_base = patient_args
    
    try:
        dicom_path = os.path.join(ct_base, patient_id, "PRE")
        mask_path = os.path.join(seg_base, patient_id, "PRE", "pancreas.nii.gz")
        output_file = os.path.join(output_base, f"{patient_id}_PRE_rtstruct.dcm")

        # 1. 경로 유효성 검사
        if not os.path.exists(dicom_path):
            raise FileNotFoundError(f"DICOM 경로 없음: {dicom_path}")
        if not os.path.exists(mask_path):
            raise FileNotFoundError(f"Segmentation 파일 없음: {mask_path}")

        # 2. DICOM 시리즈 검증
        dicom_slices = validate_dicom_series(dicom_path)
        
        # 3. NIfTI 파일 로드
        mask_img = nib.load(mask_path)
        mask_data = mask_img.get_fdata()
        
        # 4. 좌표계 일치 여부 검증
        validate_coordinate_system(dicom_slices, mask_img)
        
        # 5. 슬라이스 수 일치 검증
        if len(dicom_slices) != mask_data.shape[2]:
            raise ValueError(
                f"슬라이스 수 불일치 (DICOM: {len(dicom_slices)}, NIfTI: {mask_data.shape[2]})"
            )

        # 6. 이진 마스크 생성
        binary_mask = mask_data > 0
        
        # 7. RTStruct 생성
        rtstruct = RTStructBuilder.create_new(dicom_series_path=dicom_path)
        rtstruct.add_roi(mask=binary_mask, name="Pancreas")
        rtstruct.save(output_file)

        return (patient_id, "성공", output_file)
        
    except Exception as e:
        return (patient_id, f"실패: {str(e)}", None)

def main():
    print("RTSTRUCT 생성기")
    
    # 경로 입력 및 검증
    ct_base = os.path.normpath(input("CT DICOM 루트 경로: ").strip().strip('"'))
    seg_base = os.path.normpath(input("Segmentation 루트 경로: ").strip().strip('"'))
    output_base = os.path.normpath(input("출력 루트 경로: ").strip().strip('"'))

    # 보안 검증
    if os.path.commonpath([ct_base, output_base]) == ct_base:
        raise ValueError("출력 경로가 입력 경로 내에 있습니다")
    
    # 환자 목록 준비
    patients = [
        (folder, ct_base, seg_base, output_base)
        for folder in os.listdir(ct_base)
        if folder.isdigit() and os.path.isdir(os.path.join(ct_base, folder))
    ]

    # 병렬 처리
    with multiprocessing.Pool() as pool:
        results = list(tqdm(
            pool.imap(process_patient, patients),
            total=len(patients),
            desc="환자 처리 진행 상황"
        ))

    # 결과 요약
    print("\n처리 결과:")
    success = 0
    for pid, status, path in results:
        print(f"- {pid}: {status}")
        if status == "성공":
            success += 1
            
    print(f"\n성공: {success}/{len(patients)}, 실패: {len(patients)-success}")

if __name__ == "__main__":
    main()
