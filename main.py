import json
import time

EPSILON = 1e-9


def validate_matrix(matrix, size):                      # 필터/패턴 N x N 구조 체크
    if len(matrix) != size:
        return False
    for row in matrix:
        if len(row) != size:
            return False
    return True


def mac_operation(pattern, filter_matrix):              # MAC 연산
    size = len(pattern)
    total = 0.0

    for i in range(size):
        for j in range(size):
            total += pattern[i][j] * filter_matrix[i][j]

    return total


def compare_scores(score_cross, score_x, epsilon=EPSILON):  # 점수 비교
    diff = abs(score_cross - score_x)

    if diff < epsilon:
        return "UNDECIDED"
    elif score_cross > score_x:
        return "A"
    else:
        return "B"


def input_matrix_3x3(prompt):                           # 사용자 입력 검증 처리
    print(prompt)

    while True:                                         # 입력 변환 및 데이터 구조화
        rows = []
        for _ in range(3):
            rows.append(input())
        try:
            matrix = []
            for line in rows:       
                row = [float(x) for x in line.split()]
                matrix.append(row)

            if not validate_matrix(matrix, 3):
                print("입력 형식 오류: 각 줄에 3개의 숫자를 입력하세요.")
                continue
            return matrix

        except ValueError:
            print("입력 형식 오류: 숫자를 입력해야 합니다.")


def measure_mac_time(pattern, filter_matrix, repeat=10):    # 연산 성능 측정
    start = time.time()
    for _ in range(repeat):
        mac_operation(pattern, filter_matrix)
    end = time.time()
    return (end - start) / repeat * 1000


def run_user_mode():                                        # 1.사용자 모드
    print("\n#---------------------------------------")
    print("# [1] 필터 입력")
    print("#---------------------------------------")
    filter_a = input_matrix_3x3("필터 A 입력 (3줄)")
    filter_b = input_matrix_3x3("필터 B 입력 (3줄)")

    print("\n#---------------------------------------")
    print("# [2] 패턴 입력")
    print("#---------------------------------------")
    pattern = input_matrix_3x3("패턴 입력 (3줄)")

    score_a = mac_operation(pattern, filter_a)
    score_b = mac_operation(pattern, filter_b)
    result = compare_scores(score_a, score_b)
    avg_time = measure_mac_time(pattern, filter_a)

    print("\n#---------------------------------------")
    print("# [3] MAC 결과")
    print("#---------------------------------------")
    print(f"A 점수: {score_a}")
    print(f"B 점수: {score_b}")
    print(f"연산 시간(평균/10회): {avg_time:.3f} ms")

    if result == "UNDECIDED":
        print("판정: 판정 불가 (|A-B| < epsilon)")
    else:
        print(f"판정: {result}")


def load_filters(data):                                 # 파일 내용 중 필터만 저장
    filters = {}

    for size_key, value in data["filters"].items():
        size = int(size_key.split("_")[1])

        filters[size] = {
            "Cross": value["cross"],
            "X": value["x"]
        }

    return filters


def normalize_label(label):                             # 라벨 정규화
    label = label.strip().lower()

    if label in ["+", "cross"]:
        return "Cross"
    elif label in ["x"]:
        return "X"
    else:
        raise ValueError(f"알 수 없는 라벨: {label}")


def evaluate_patterns(data, filters):                       # JSON 평가
    results = []

    for key, item in data["patterns"].items():
        try:
            size = int(key.split("_")[1])

            if size not in filters:
                raise ValueError("필터 없음")

            pattern = item["input"]

            if not validate_matrix(pattern, size):
                raise ValueError("패턴 크기 불일치")

            filter_cross = filters[size]["Cross"]
            filter_x = filters[size]["X"]

            score_cross = mac_operation(pattern, filter_cross)
            score_x = mac_operation(pattern, filter_x)

            if compare_scores(score_cross, score_x) == "A":     
                predicted = "Cross"
            elif compare_scores(score_cross, score_x) == "B":
                predicted = "X"
            else:
                predicted = "UNDECIDED"
            expected = normalize_label(item["expected"])

            if predicted == "UNDECIDED":
                status = "FAIL (동점 규칙)"
            elif predicted == expected:
                status = "PASS"
            else:
                status = "FAIL"

            results.append({
                "key": key,
                "score_cross": score_cross,
                "score_x": score_x,
                "predicted": predicted,
                "expected": expected,
                "status": status
            })

        except Exception as e:
            results.append({
                "key": key,
                "status": "FAIL",
                "reason": str(e)
            })

    return results


def print_results(results, filters):                                     # 결과 출력
    print("\n#---------------------------------------")
    print("# [2] 패턴 분석 (라벨 정규화 적용)")
    print("#---------------------------------------")

    for r in results:
        print(f"\n--- {r['key']} ---")

        if r["status"] == "FAIL" and "reason" in r:
            print(f"FAIL ({r['reason']})")
            continue

        print(f"Cross 점수: {r['score_cross']}")
        print(f"X 점수: {r['score_x']}")
        print(f"판정: {r['predicted']} | expected: {r['expected']} | {r['status']}")

    print("\n#---------------------------------------")
    print("# [3] 성능 분석 (평균/10회)")
    print("#---------------------------------------")
    print("크기       평균 시간(ms)    연산 횟수")
    print("-------------------------------------")

    for size, f in filters.items():
        pattern = f["Cross"]
        avg_time = measure_mac_time(pattern, f["Cross"])
        print(f"{size}×{size}    {avg_time:.3f} ms    {size*size}")

    total = len(results)
    passed = sum(1 for r in results if r["status"] == "PASS")
    failed = total - passed

    print("\n#---------------------------------------")
    print("# [4] 결과 요약")
    print("#---------------------------------------")
    print(f"총 테스트: {total}")
    print(f"통과: {passed}")
    print(f"실패: {failed}")

    print("\n실패 케이스:")
    for r in results:
        if r["status"] == "FAIL (동점 규칙)":
            print(f"- {r['key']}: 동점(UNDECIDED) 처리 규칙에 따라 FAIL")
        elif r["status"] == "FAIL":
            if "reason" in r:
                print(f"- {r['key']}: {r['reason']}")
            else:
                print(f"- {r['key']}: 예측 불일치")


def run_json_mode():                                         # 2.JSON 모드
    try:
        with open("data.json", "r", encoding="utf-8") as f:     # JSON 읽기
            data = json.load(f)
    except FileNotFoundError:
        print("파일을 찾을 수 없습니다.")
        data = None
    except json.JSONDecodeError:
        print("JSON 형식 오류")
        data = None

    if data is None:
        return

    if "filters" not in data or "patterns" not in data:
        print("JSON 구조 오류")
        return
    
    filters = load_filters(data)

    print("\n#---------------------------------------")
    print("# [1] 필터 로드")
    print("#---------------------------------------")

    for size in filters:
        print(f"✓ size_{size} 필터 로드 완료 (Cross, X)")

    results = evaluate_patterns(data, filters)

    print_results(results, filters)


def main():                                              # 메인
    print("=== Mini NPU Simulator ===")
    print("1. 사용자 입력 (3x3)")
    print("2. data.json 분석")

    choice = input("선택: ")

    if choice == "1":
        run_user_mode()
    elif choice == "2":
        run_json_mode()
    else:
        print("잘못된 선택")

if __name__ == "__main__":
    main()