# 유니티 C# 스타일 상세 규칙

## 목차
1. [K&R 중괄호 스타일](#kr-중괄호-스타일)
2. [try-catch 예외처리](#try-catch-예외처리)
3. [한글 주석 규칙](#한글-주석-규칙)
4. [유니티 특화 주의사항](#유니티-특화-주의사항)

## K&R 중괄호 스타일

C#의 일반 관례는 Allman(여는 중괄호를 새 줄에)이지만, **이 프로젝트는 K&R을 따른다** — 여는 중괄호는 같은 줄 끝에, 닫는 중괄호는 자기 줄에 둔다. IDE 자동 포맷이 Allman으로 되돌리는 경우가 많으니 생성/수정한 코드가 K&R인지 항상 확인한다.

```csharp
// 올바른 K&R 스타일
public class PlayerController : MonoBehaviour {
    private Rigidbody _rb;

    private void Awake() {
        try {
            _rb = GetComponent<Rigidbody>();
        } catch (Exception e) {
            Debug.LogError($"Rigidbody 초기화 실패: {e.Message}");
        }
    }

    public void Move(Vector3 direction) {
        if (direction == Vector3.zero) {
            return;
        }
        _rb.AddForce(direction * _speed);
    }
}
```

세부 규칙:
- 클래스, 메서드, 프로퍼티, 제어문(if/for/while/switch) 모두 여는 중괄호를 같은 줄에 둔다.
- `else`, `catch`, `finally`는 닫는 중괄호와 같은 줄에 둔다: `} else {`, `} catch (Exception e) {`
- 한 줄짜리 if라도 중괄호를 생략하지 않는다 (버그 예방).
- 들여쓰기는 스페이스 4칸.

## try-catch 예외처리

**실패할 수 있는 외부 의존 작업을 수행하는 함수는 try-catch로 감싼다.** 목적은 게임 루프가 한 번의 예외로 죽지 않게 하고, 실패 지점을 로그로 즉시 알 수 있게 하는 것이다.

```csharp
public bool SaveGame(SaveData data) {
    try {
        string json = JsonUtility.ToJson(data);
        File.WriteAllText(_savePath, json);
        return true;
    } catch (IOException e) {
        Debug.LogError($"세이브 파일 쓰기 실패: {e.Message}");
        return false;
    } catch (Exception e) {
        Debug.LogError($"세이브 중 알 수 없는 오류: {e.Message}");
        return false;
    }
}
```

세부 규칙:
- catch 블록은 구체적인 예외부터 잡고 마지막에 `Exception`으로 받는다.
- catch에서 반드시 `Debug.LogError`(또는 프로젝트 로거)로 **한글 메시지 + 예외 내용**을 남긴다. 빈 catch(예외 삼키기)는 금지.
- 실패를 호출자가 알아야 하면 bool/null/Result 형태로 반환하고, 복구 불가능한 상황이면 로그 후 `throw`로 다시 던진다.
- 단순 연산만 하는 순수 함수(수학 계산, 값 변환 등 외부 의존이 없는 것)까지 기계적으로 감쌀 필요는 없다 — try-catch는 I/O, 파싱, 컴포넌트 접근, 네트워크, 리소스 로드처럼 **실제로 실패할 수 있는 지점**에 건다.
- `Update()` 등 매 프레임 호출되는 경로의 try-catch는 GC/성능 영향은 거의 없지만, 매 프레임 같은 에러가 로그를 도배하지 않도록 플래그로 1회만 로깅하는 것을 고려한다.

## 한글 주석 규칙

주석은 **한글로, 한 줄 이내로, 간략하고 알기 쉽게** 작성한다.

```csharp
// 점프 가능 여부를 지면 접촉으로 판단
private bool CanJump() {
    return _isGrounded && !_isStunned;
}
```

세부 규칙:
- "무엇을 하는지"가 아니라 코드만으로 알기 어려운 **의도/이유**를 적는다. 자명한 코드에는 주석을 달지 않는다.
- 메서드 위 한 줄 `//` 주석을 기본으로 한다. public API라 IDE 툴팁이 필요한 경우에만 `/// <summary>`를 쓰되, summary 내용도 한글 한 줄로 한다.
- 영어 주석, 여러 줄 설명, 장식용 구분선 주석(`// =====`)은 쓰지 않는다.
- TODO는 `// TODO: 내용` 형식으로 한글 한 줄.

## 유니티 특화 주의사항

- `GetComponent` 결과는 null일 수 있으므로 try-catch보다 null 체크가 자연스러운 경우가 많다 — 예외가 나는 작업(파일, JSON, 네트워크)에 try-catch, 없을 수 있는 참조에 null 체크를 쓴다.
- 코루틴 내부 예외는 코루틴만 죽이므로, 코루틴 안의 위험 작업도 try-catch로 감싼다 (단, `yield return`은 try 블록 안에 둘 수 없으니 위험 구간만 분리해서 감싼다).
- `UnityEvent`/콜백에 연결되는 핸들러는 예외가 다른 리스너 실행을 막을 수 있으므로 내부에서 try-catch 처리한다.
