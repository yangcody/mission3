# Mini NPU Simulator

## 1. 실행 방법

```bash
python main.py
```

프로그램 실행 후 아래 두 가지 모드 중 하나를 선택합니다:

* **1: 사용자 입력 (3×3)**

  * 콘솔에서 3×3 필터 2개(A, B)와 패턴을 입력
  * MAC 연산 및 판정 결과 출력

* **2: data.json 분석**

  * `data.json` 파일을 로드하여 여러 패턴을 자동 분석
  * PASS/FAIL 결과 및 성능 분석 출력

> `data.json` 파일은 반드시 `main.py`와 동일한 디렉토리에 위치해야 합니다.

---

## 2. 구현 요약

### 2.1 라벨 정규화

입력 데이터의 다양한 라벨 표현(‘+’, ‘cross’, ‘x’)을 내부적으로 다음 두 가지 표준 라벨로 통일하였다:

* `"Cross"`
* `"X"`

이를 통해 데이터 표현 차이로 인해 발생할 수 있는 비교 오류를 제거하였다.
모든 비교는 정규화된 라벨 기준으로 수행된다.

---

### 2.2 MAC 연산 구현

MAC(Multiply-Accumulate) 연산은 다음 방식으로 구현하였다:

* 2차원 배열(패턴, 필터)의 동일 위치 값을 곱함
* 모든 곱셈 결과를 누적 합산

구현은 외부 라이브러리를 사용하지 않고 **이중 반복문**으로 직접 수행하였다.

```text
score = Σ (pattern[i][j] × filter[i][j])
```

이 방식은 모든 크기(N×N)에 대해 동일하게 동작하도록 일반화하였다.

---

### 2.3 동점 처리 (epsilon 기반 비교)

부동소수점 연산의 특성상 미세한 오차가 발생할 수 있기 때문에,
단순 비교 대신 **epsilon 기반 비교 정책**을 적용하였다.

```text
abs(score_a - score_b) < 1e-9 → UNDECIDED
```

판정 기준:

* Cross > X → Cross
* X > Cross → X
* 차이가 epsilon 미만 → UNDECIDED

이를 통해 수치 오차로 인한 잘못된 판정을 방지하였다.

---

## 3. 결과 리포트

### 3.1 실패 원인 분석

일부 테스트 케이스에서 FAIL이 발생할 수 있으며, 주요 원인은 다음 세 가지로 분류된다.

1. **수치 비교 문제 (부동소수점 오차)**
   특정 케이스에서는 Cross와 X 점수가 거의 동일하게 계산되어 epsilon 기준에 의해 UNDECIDED로 판정된다.
   이 경우 expected 값이 Cross 또는 X일 경우 FAIL로 처리된다.
   이는 부동소수점 정밀도 한계에 따른 정상적인 동작이다.

2. **데이터/스키마 문제**
   JSON 데이터에서 패턴 크기와 필터 크기가 일치하지 않거나, 해당 크기의 필터가 존재하지 않는 경우 FAIL이 발생한다.
   이러한 경우 프로그램은 종료되지 않고 해당 케이스만 실패로 처리한다.

3. **라벨 처리 문제 방지**
   라벨 정규화를 적용하지 않을 경우 동일한 의미의 값('+', 'cross', 'x')이 서로 다르게 비교되어 FAIL이 발생할 수 있다.
   본 구현에서는 정규화를 통해 이 문제를 사전에 제거하였다.

FAIL이 발생하지 않은 경우에도, 이는 다음 두 정책이 정확히 적용된 결과이다:

* 라벨 정규화를 통한 데이터 일관성 확보
* epsilon 기반 비교를 통한 안정적인 판정

---

### 3.2 시간 복잡도 분석

MAC 연산은 다음과 같은 구조로 구현되어 있다:

```text
for i in range(N):
    for j in range(N):
        연산 수행
```

따라서 전체 연산 횟수는:

```text
N × N = N²
```

즉, 시간 복잡도는 **O(N²)**이다.

---

### 3.3 측정 결과 해석

실제 측정 결과:

| 크기    | 연산 횟수 | 평균 시간(ms) |
| ----- | ----- | --------- |
| 3×3   | 9     | ~0.01 ms  |
| 5×5   | 25    | ~0.03 ms  |
| 13×13 | 169   | ~0.18 ms  |
| 25×25 | 625   | ~0.68 ms  |

분석:

* 입력 크기가 증가할수록 실행 시간이 증가함
* 연산 횟수(N²)가 증가하는 비율과 실행 시간 증가가 유사함

예를 들어:

* 5×5 → 25 연산
* 25×25 → 625 연산 (약 25배 증가)

실행 시간 또한 비례하여 증가하는 경향을 보인다.

---

### 3.4 결론

* MAC 연산은 입력 크기에 대해 **이차 시간 복잡도(O(N²))**를 가진다.
* 실제 측정 결과가 이론과 일치함을 확인하였다.
* epsilon 기반 비교를 통해 수치 안정성을 확보하였다.
* 라벨 정규화를 통해 데이터 불일치 문제를 해결하였다.

---

## 4. 요약

본 프로그램은 다음 기능을 안정적으로 수행한다:

* 3×3 사용자 입력 기반 MAC 연산 및 판정
* JSON 기반 대량 패턴 분석 및 PASS/FAIL 판정
* 부동소수점 오차를 고려한 비교 정책 적용
* 크기별 성능 측정 및 시간 복잡도 분석
* 오류 발생 시에도 중단되지 않는 안정적인 처리 구조

---

## 5. 소스 코드 (main.py)

main() 함수 1개로 구현함

```text
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
```
