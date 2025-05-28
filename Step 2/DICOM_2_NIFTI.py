import os
import re
import dicom2nifti
import dicom2nifti.settings
import nibabel as nib

##DICOM 시리즈가 갖고 있는 모든 데이터를 만들어서 추후 히스토그램이나 RT Structure로 재구성할 때 필요한 파일 

##환자 번호를 일렬로 세워 추후 다루기 쉽게  
def extract_patient_id(path: str) -> str:
    match = re.findall(r"\d+", path)
    return match[-1].zfill(3) if match else "000"

def convert_dicom_folder(dicom_folder: str, output_base: str, phase: str):
    if not os.path.isdir(dicom_folder):
        print(f"다이콤 폴더가 아님: {dicom_folder}")
        return

    patient_id = extract_patient_id(dicom_folder)
    output_folder = os.path.join(output_base, patient_id)
    os.makedirs(output_folder, exist_ok=True)

    ##nii.gz 파일을 압축 풀기
    temp_nii_gz = os.path.join(output_folder, f"{patient_id}_{phase}.nii.gz")
    final_nii = temp_nii_gz.replace(".nii.gz", ".nii")

    if os.path.exists(final_nii):
        print(f"이미 변환됨: {final_nii}")
        return
      
    ##reorientation이 중요해서 convert_directiory 사용
    try:
        dicom2nifti.convert_directory(dicom_folder, output_folder, reorient=True)

        
        for f in os.listdir(output_folder):
            if f.endswith(".nii.gz"):
                temp_path = os.path.join(output_folder, f)
                img = nib.load(temp_path)
                nib.save(img, final_nii)
                os.remove(temp_path)
                print(f"변환 완료: {final_nii}")
                return

        print(f"NIfTI 파일을 찾을 수 없어ㅠㅠㅠㅠㅠㅠ: {dicom_folder}")
    except Exception as e:
        print(f"변신하다 공격 받음: {dicom_folder} - {e}")

def for_batch_convert_all_patients():
    root_folder = input("DICOM 루트 폴더 입력: ").strip('"').strip()
    phase = input("PRE냐 POST냐 그것이 문제로다: ").strip().upper()
    output_base = input("출력 폴더 입력: ").strip('"').strip()

    if not output_base:
        output_base = os.path.join(os.getcwd(), "converted_output")

    if not os.path.isdir(root_folder):
        print(f"잘못된 DICOM 루트 경로: {root_folder}")
        return

    if phase not in ("PRE", "POST"):
        print("PRE 또는 POST만 입력 가능")
        return

    dicom2nifti.settings.disable_validate_slice_increment()
    os.makedirs(output_base, exist_ok=True)

    for name in sorted(os.listdir(root_folder)):
        patient_folder = os.path.join(root_folder, name)
        phase_folder = os.path.join(patient_folder, phase)
        if os.path.isdir(phase_folder):
            print(f"변환: {phase_folder}")
            convert_dicom_folder(phase_folder, output_base, phase)

if __name__ == "__main__":
    for_convert_all_patients()

