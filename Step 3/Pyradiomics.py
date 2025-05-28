import os
import SimpleITK as sitk
from radiomics import featureextractor
import pandas as pd

##둘 다 NifTI 파일로 데이터를 불러와 Radiomics를 추출할 수 있지만 축 일치 문제를 고려했을 때 SimpleITK를 둘 다 적용해 
##사전에 생길 수 있는 문제를 차단하고자 함 

def load_image(image_path):
    if os.path.isdir(image_path):
        reader = sitk.ImageSeriesReader()
        dicom_names = reader.GetGDCMSeriesFileNames(image_path)
        reader.SetFileNames(dicom_names)
        image = reader.Execute()
    elif image_path.endswith(('.nii', '.nii.gz')):
        image = sitk.ReadImage(image_path)
    else:
        raise ValueError("DICOM 이미지가 아닌데...")
    return image

def run_extraction(image_path, mask_path, param_path=None, output_csv=None):
    image = load_image(image_path)
    mask = sitk.ReadImage(mask_path)
    mask.CopyInformation(image)

    ##parameters를 정의, yaml 경로 
    if param_path and os.path.exists(param_path):
        extractor = featureextractor.RadiomicsFeatureExtractor(param_path)
        print(f"너로 정했다: {param_path}")
    else:
        extractor = featureextractor.RadiomicsFeatureExtractor()
        print("선택 장애는 기본이 좋아")

    # 특징 추출, label 값을 정해야 하는데 각각의 label마다 매칭되는 장기가 존재, 췌장은 7
    result = extractor.execute(image, mask, label = 7)

    print("\n라디오 믹스 나온당:")
    for key, val in result.items():
        print(f"{key}: {val}")

    #cmd 창에만 나오는 걸 모두 엑셀로 저장 
    if output_csv:
        # 디렉토리가 없다면 생성
        output_dir = os.path.dirname(output_csv)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir)
            print(f"이곳으로 들어가 보아요: {output_dir}")

        df = pd.DataFrame([result])
        df.to_csv(output_csv, index=False)
        print(f"\n엑셀 저장 완료: {output_csv}")

def main():
    print("PyRadiomics 특징 추출기")
    image_path = input("DICOM 파일들 있는 곳: ").strip()
    mask_path = input("원하는 장기 마스크 파일 경로: ").strip()
    param_path = input("YAML 파일 경로 입해요: ").strip()
    output_csv = input("결과 얻을 곳: ").strip()

    run_extraction(
        image_path=image_path,
        mask_path=mask_path,
        param_path=param_path if param_path else None,
        output_csv=output_csv if output_csv else None
    )

if __name__ == "__main__":
    main()
