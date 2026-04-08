from matrix import Matrix
from engine import Engine
from data_loader import DataLoader

class Application:
    def __init__(self):
        self.engine = Engine()
        self.loader = DataLoader()

    def run(self):
        print("=== Mini NPU Simulator ===")
        print("1. 사용자 입력 (3x3)")
        print("2. data.json 분석")

        choice = input("선택: ")
        if choice == "1":
            self.run_user_mode()
        elif choice == "2":
            self.run_json_mode()
        else:
            print("잘못된 선택")

    def run_user_mode(self):                                        # 사용자 입력 모드
        print("\n#---------------------------------------")
        print("# [1] 필터 입력")
        print("#---------------------------------------")

        filter_a = Matrix.from_input(3, "필터 A (3줄 입력, 공백 구분)")
        filter_b = Matrix.from_input(3, "필터 B (3줄 입력, 공백 구분)")

        print("\n#---------------------------------------")
        print("# [2] 패턴 입력")
        print("#---------------------------------------")

        pattern = Matrix.from_input(3, "패턴 (3줄 입력, 공백 구분)")

        score_a = self.engine.mac(pattern, filter_a)
        score_b = self.engine.mac(pattern, filter_b)

        result = self.engine.compare(score_a, score_b)              # 판정 결과 계산
        avg_time = self.engine.measure_time(pattern, filter_a)      # 성능 측정 (평균 시간 계산)

        print("\n#---------------------------------------")
        print("# [3] MAC 결과")
        print("#---------------------------------------")
        print(f"A 점수: {score_a}")
        print(f"B 점수: {score_b}")

        if result == "UNDECIDED":
            print("판정: 판정 불가 (|A-B| < epsilon 1e-9)")
        else:
            print(f"연산 시간(평균/10회): {avg_time:.3f} ms")
            print(f"판정: {result}")

    def run_json_mode(self):                                        # data.json 분석 모드
        data = self.loader.load_json("data.json")
        if data is None:
            return

        if "filters" not in data or "patterns" not in data:
            print("JSON 구조 오류")
            return

        filters = self.loader.load_filters(data)

        print("\n#---------------------------------------")
        print("# [필터 로드]")
        print("#---------------------------------------")
        for size in filters:
            print(f"✓ size_{size} 필터 로드 완료 (Cross, X)")

        results = []

        for key, item in data["patterns"].items():
            try:
                size = self.loader.extract_size(key)

                if size not in filters:
                    raise ValueError("필터 없음")

                pattern = Matrix(item["input"])

                if not Matrix._validate(pattern.data, size):
                    raise ValueError("패턴 크기 불일치")

                filter_cross = filters[size]["Cross"]
                filter_x = filters[size]["X"]

                score_cross = self.engine.mac(pattern, filter_cross)
                score_x = self.engine.mac(pattern, filter_x)

                predicted = self.engine.compare(score_cross, score_x)
                expected = self.loader.normalize_label(item["expected"])

                status = "PASS" if predicted == expected else "FAIL"

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

        self._print_results(results)
        self._print_performance(filters)
        self._print_summary(results)

    # -------------------------
    # 출력 관련 메서드
    # -------------------------
    def _print_results(self, results):
        print("\n#---------------------------------------")
        print("# [패턴 분석 결과]")
        print("#---------------------------------------")

        for r in results:
            print(f"\n--- {r['key']} ---")

            if r["status"] == "FAIL" and "reason" in r:
                print(f"FAIL ({r['reason']})")
                continue

            print(f"Cross 점수: {r['score_cross']}")
            print(f"X 점수: {r['score_x']}")
            print(f"판정: {r['predicted']} | expected: {r['expected']} | {r['status']}")

    def _print_performance(self, filters):
        print("\n#---------------------------------------")
        print("# [성능 분석]")
        print("#---------------------------------------")

        print("크기       평균 시간(ms)    연산 횟수")
        print("-------------------------------------")

        for size, f in filters.items():
            avg_time = self.engine.measure_time(f["Cross"], f["Cross"])
            print(f"{size}×{size}    {avg_time:.3f} ms    {size*size}")

    def _print_summary(self, results):
        total = len(results)
        passed = sum(1 for r in results if r["status"] == "PASS")
        failed = total - passed

        print("\n#---------------------------------------")
        print("# [결과 요약]")
        print("#---------------------------------------")
        print(f"총 테스트: {total}")
        print(f"통과: {passed}")
        print(f"실패: {failed}")

        print("\n실패 케이스:")
        for r in results:
            if r["status"] == "FAIL":
                if "reason" in r:
                    print(f"- {r['key']}: {r['reason']}")
                else:
                    print(f"- {r['key']}: 예측 불일치")