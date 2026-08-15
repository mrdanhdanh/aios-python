# TASK-043 — Critique v2

## Phản biện độc lập
- **P1-01 Public namespace**: chỉ export symbols chủ ý qua `aios.__all__`; không leak implementation.
- **P1-02 Response contract**: Client phải validate transport response thành DTO, không trả raw object không kiểm soát.
- **P2-01 Subclass contract**: Agent/Tool phải có id hợp lệ; Tool phải có ít nhất một capability; Workflow phải có node.
- **P2-02 Cycle implementation**: DAG validation phải có self-loop và cycle nhiều node, không chỉ kiểm tra số cạnh.
- **P2-03 Transport compatibility**: transport methods nhận operation payload rõ ràng, mock dễ thay thế.
- **P3-01 Documentation**: README phải nêu SDK không thay thế Policy/Runtime và quickstart không side effect.

## Resolution
- ✅ `__all__` giới hạn ở API v1.
- ✅ Client chuẩn hóa response qua DTO constructors.
- ✅ Base class validation chạy khi khởi tạo/subclass instance.
- ✅ Kahn topological sort phát hiện mọi cycle.
- ✅ Protocol transport có 4 method typed.
- ✅ README ghi rõ boundary và ví dụ mock transport.
