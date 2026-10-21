# ============================================================
# 【这个文件是干什么的】
# 支付相关的接口。
# ============================================================

from decimal import Decimal

from fastapi import APIRouter, Query, Request
from fastapi.responses import HTMLResponse

from app.api.deps import DbDep, PaymentServiceDep
from app.schemas import (
    ApiResponse,
    PaymentCreate,
    PaymentCreateResult,
)

router = APIRouter(prefix="/payments", tags=["支付"])


# ════════════════════════════════════════════════════════════
# 【发起支付】
# ════════════════════════════════════════════════════════════

@router.post(
    "/create",
    response_model=ApiResponse[PaymentCreateResult],
    summary="发起支付",
    description="创建支付单，返回前端调起支付需要的参数",
)
async def create_payment(data: PaymentCreate, service: PaymentServiceDep):
    """
    【干什么】用户点「去支付」时调用。

    【返回什么】
        真实环境：微信/支付宝的预支付参数
        当前 Mock：一个假收银台地址 mock_pay_url
    """
    result = await service.create_payment(data)
    return ApiResponse(data=result)


# ════════════════════════════════════════════════════════════
# 【Mock 收银台】
#
# 【以后要删掉】
# 接入真实支付后，这个是微信/支付宝的收银台，不是我们的页面。
# ════════════════════════════════════════════════════════════

@router.get(
    "/mock/pay",
    response_class=HTMLResponse,
    summary="【Mock】模拟收银台页面",
    include_in_schema=False,   # 不在接口文档里显示
)
async def mock_pay_page(order_no: str):
    """
    【干什么】显示一个假的付款页面。

    【真实环境不存在这个页面】
    真实环境是跳转到微信/支付宝的官方收银台。
    """
    html = f"""
    <!DOCTYPE html>
    <html lang="zh-CN">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width,initial-scale=1">
        <title>模拟支付</title>
        <style>
            * {{ margin: 0; padding: 0; box-sizing: border-box; }}
            body {{
                font-family: -apple-system, "PingFang SC", sans-serif;
                background: #FDFBF8;
                padding: 40px 24px;
                text-align: center;
                color: #1A1512;
            }}
            .box {{
                max-width: 380px;
                margin: 0 auto;
                background: #fff;
                padding: 36px 24px;
                border: 1px solid #EBE6DF;
            }}
            h1 {{ font-size: 17px; font-weight: 500; margin-bottom: 10px; }}
            .order {{ font-size: 12px; color: #6B6259; margin-bottom: 24px; font-family: monospace; }}
            .amt {{ font-size: 32px; margin: 24px 0 32px; font-weight: 500; color: #8B5E3C; }}
            .btn {{
                display: block; padding: 15px;
                background: #8B5E3C; color: #fff;
                text-decoration: none; font-size: 15px;
                margin-bottom: 12px; border-radius: 2px;
            }}
            .cancel {{ display: block; padding: 12px; color: #6B6259; text-decoration: none; font-size: 13px; }}
            .tip {{ margin-top: 28px; font-size: 11px; color: #A69C92; line-height: 1.9; }}
        </style>
    </head>
    <body>
        <div class="box">
            <h1>模拟支付</h1>
            <div class="order">{order_no}</div>
            <div class="amt">¥<span id="amt">--</span></div>
            <a class="btn" href="/api/v1/payments/mock/success?order_no={order_no}">确认支付</a>
            <a class="cancel" href="/">取消</a>
            <div class="tip">
                这是测试环境的模拟收银台<br>
                接入真实支付后由官方收银台替代
            </div>
        </div>
        <script>
            fetch('/api/v1/orders/{order_no}')
                .then(r => r.json())
                .then(d => {{
                    if (d.data) {{
                        document.getElementById('amt').textContent = d.data.pay_amount;
                    }}
                }});
        </script>
    </body>
    </html>
    """
    return HTMLResponse(html)


@router.get(
    "/mock/success",
    summary="【Mock】模拟支付成功",
    include_in_schema=False,
)
async def mock_pay_success(order_no: str, db: DbDep):
    """
    【干什么】用户点了「确认支付」→ 假装支付成功 → 走真实回调逻辑。

    【真实环境不存在】
    真实环境是支付网关主动 POST 到 /payments/callback。
    """
    from fastapi.responses import RedirectResponse
    from app.repositories import OrderRepository
    from app.services import PaymentService

    order_repo = OrderRepository(db)
    order = await order_repo.get_by_order_no(order_no, with_items=False, with_logs=False)

    if order is None:
        from app.core.exceptions import NotFoundError
        raise NotFoundError("订单不存在")

    service = PaymentService(db)
    await service.handle_callback(
        order_no=order_no,
        channel="mock",
        trade_no="MOCK" + __import__("uuid").uuid4().hex[:12].upper(),
        amount=order.pay_amount,
        success=True,
        raw={"mock": True},
    )

    # 跳转到订单状态页
    return RedirectResponse(f"/orders/{order_no}", status_code=302)


# ════════════════════════════════════════════════════════════
# 【支付回调】
#
# 【真实环境谁调这个】
# 微信/支付宝的服务器会 POST 到这里。
#
# 【生产环境必须做验签】
# 现在的 Mock 适配器不验签，生产环境必须换真实适配器。
# ════════════════════════════════════════════════════════════

@router.post(
    "/callback",
    response_model=ApiResponse[dict],
    summary="支付回调",
    description="支付网关回调接口。生产环境必须验签。",
)
async def payment_callback(
    request: Request,
    db: DbDep,
):
    """
    【干什么】接收支付结果。

    【幂等保证】
    重复回调不会重复处理（Service 层做了检查）。

    【生产环境要做的事】
    1. 调 adapter.verify_callback() 验签
    2. 验签失败直接返回 403
    3. 现在 Mock 适配器跳过验签 —— 上线前必须改
    """
    from app.adapters.payment import get_payment_adapter
    from app.services import PaymentService

    adapter = get_payment_adapter()
    body_bytes = await request.body()
    headers = dict(request.headers)

    # ── 验签 ──
    is_valid = await adapter.verify_callback(headers, body_bytes)
    if not is_valid:
        from app.core.exceptions import ForbiddenError
        raise ForbiddenError("回调验签失败")

    # ── 解析 ──
    parsed = await adapter.parse_callback(body_bytes)

    # ── 处理 ──
    service = PaymentService(db)
    result = await service.handle_callback(
        order_no=parsed["order_no"],
        channel=headers.get("x-channel", "mock"),
        trade_no=parsed.get("trade_no", ""),
        amount=Decimal(str(parsed["amount"])),
        success=parsed.get("success", True),
        raw=parsed.get("raw"),
    )

    return ApiResponse(data=result.model_dump())


# ════════════════════════════════════════════════════════════
# 【查询支付记录】
# ════════════════════════════════════════════════════════════

@router.get(
    "/records/{order_no}",
    response_model=ApiResponse[list],
    summary="查支付记录",
    description="一个订单可能有多次支付尝试，返回全部记录",
)
async def get_payment_records(order_no: str, db: DbDep):
    """
    【干什么】查这个订单的所有支付尝试。

    【什么时候用】
    用户说「我付了钱但订单没变」，查这个看支付到底成没成。
    """
    from app.repositories import PaymentRepository

    repo = PaymentRepository(db)
    payments = await repo.list_by_order(order_no)

    return ApiResponse(data=[
        {
            "id": p.id,
            "channel": p.channel,
            "amount": str(p.amount),
            "status": p.status,
            "trade_no": p.trade_no,
            "paid_at": p.paid_at,
            "created_at": p.created_at.strftime("%Y-%m-%d %H:%M:%S"),
        }
        for p in payments
    ])
