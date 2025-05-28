import os
import subprocess
import sys
from tqdm import tqdm

##주어진 경로에서 하위 파일을 f로 잡아 f 파일을 읽을 때 .dcm으로 끝나는 것들만 파일로 인식
def validate_dicom_folder(folder_path: str) -> bool:
    for f in os.listdir(folder_path):
        if f.lower().endswith('.dcm') or (not '.' in f):
            return True
    return False

##validate_dicom_folder에서 파일로 인정된 폴더에 대해서만 command line 사용해서 Totalsegmentator 사용
def run_segmentation(dicom_folder: str, output_path: str, organ: str):
    try:
        if not validate_dicom_folder(dicom_folder):
            print(f"DICOM 파일이 없는 것으로 보입니다: {dicom_folder}")
            return False

        segmentator_cmd = "TotalSegmentator"

        command = [
            segmentator_cmd,
            "-i", dicom_folder,
            "-o", output_path,
            "--ml",
            "--roi_subset", organ,
            "--output_type", "nifti"
        ]

        print(f"\n명령어 실행 中...: {' '.join(command)}")

        result = subprocess.run(command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        print(f"변환이 완료됐어요: {dicom_folder}")

        ##각 DICOM 파일마다 성공과 실패 여부를 확인해 txt 파일로 저장 
      
        log_file_path = os.path.join(output_path, f"{organ}_segmentation_log.txt")
        with open(log_file_path, "w", encoding="utf-8") as log_file:
            log_file.write("=== STDOUT ===\n")
            log_file.write(result.stdout)
            log_file.write("\n\n=== STDERR ===\n")
            log_file.write(result.stderr)

        return True

    except subprocess.CalledProcessError as e:
        print(f"처리 실패: {dicom_folder}")
        print("실패한 명령어:", ' '.join(e.cmd))
        print("STDOUT:\n", e.stdout)
        print("STDERR:\n", e.stderr)
        return False

    except Exception as e:
        print(f"예외 발생: {dicom_folder}")
        print(str(e))
        return False
##추후 데이터 다룰 때 .nii.gz 통일해 꺼내오기 쉽도록 전체 파일 수정 
def rename_output(output_folder: str, phase: str, organ: str, patient_id: str) -> bool:
    output_file = os.path.join(output_folder, f"{organ}.nii.gz")
    if os.path.exists(output_file):
        new_name = f"{patient_id}_{phase}_{organ}.nii.gz"
        target_path = os.path.join(output_folder, new_name)
        os.rename(output_file, target_path)
        print(f"개명 성공이에요: {target_path}")
        return True
    else:
        print(f"이름 없는 친구...: {output_file}")
        return False
      
##입출력 경로 입력 받아 위 함수들이 움직이게 하는 메인 함수
def main():
    print("파일 경로를 입력해요")
    base_path = input("시리즈가 있는 파일을 넣어보아요: ").strip()
    base_output_path = input("나왔으면 하는 폴더를 넣어보아요: ").strip()
    phase_input = input("처리할 phase를 입력해 보아요 PRE, POST, BOTH 중에서: ").strip().upper()
    organ = input("분할할 장기 이름을 입력해 보아요: ").strip().lower()

    ##슬래시 떨어트리기 
    base_path = os.path.normpath(base_path)
    base_output_path = os.path.normpath(base_output_path)

    if phase_input not in ['PRE', 'POST', 'BOTH']:
        print("PRE, POST, 또는 BOTH 중 하나를 입력해 보아요.")
        sys.exit(1)

    phases = ['PRE', 'POST'] if phase_input == 'BOTH' else [phase_input]

    if not os.path.exists(base_path):
        print(f"다시 한 번 더 경로를 확인해 보아요 ㅠㅠ: {base_path}")
        sys.exit(1)

    os.makedirs(base_output_path, exist_ok=True)
    failed_cases = []
    ##환자 폴더 이름이 숫자로 이루어질 때 선택해 DICOM 읽기 
    patient_folders = [d for d in os.listdir(base_path)
                       if os.path.isdir(os.path.join(base_path, d)) and d.isdigit()]

    for patient_id in tqdm(patient_folders, desc="전체 환자 진행률"):
        patient_folder = os.path.join(base_path, patient_id)

        for phase in phases:
            phase_folder = os.path.join(patient_folder, phase)

            if os.path.isdir(phase_folder):
                output_folder = os.path.join(base_output_path, patient_id, phase)
                os.makedirs(output_folder, exist_ok=True)

                print(f"\n 변신 중: {phase_folder} 에서 {output_folder}")
                if run_segmentation(phase_folder, output_folder, organ):
                    if not rename_output(output_folder, phase, organ, patient_id):
                        failed_cases.append(f"{patient_id}/{phase} (결과 파일 없음)")
                else:
                    failed_cases.append(f"{patient_id}/{phase} (segmentation 실패)")

    if failed_cases:
        print("\n실패한 케이스 목록:")
        for item in failed_cases:
            print(" -", item)

        failed_path = os.path.join(base_output_path, f"failed_cases_{organ}.txt")
        with open(failed_path, "w", encoding="utf-8") as f:
            for item in failed_cases:
                f.write(item + "\n")

        print(f"\n실패한 목록이 저장되었어요: {failed_path}")
    else:
        print(f"\n[{organ}] 모두 변환이 되었어요!")

if __name__ == "__main__":
    main()
