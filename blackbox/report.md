# Part 3 Black Box API Testing Report

## System Summary

Part 3 tests the QuickCart REST API as a black-box system. The test suite uses
only the published API documentation and the provided runtime image. The tests
do not inspect or modify the internal server implementation.

The automated tests are stored under `blackbox/tests/` and are grouped into:

- Header and admin validation
- Profile, addresses, and products
- Cart, coupons, and checkout
- Wallet, loyalty, and orders
- Reviews and support tickets

## How The Tests Run

The repository includes the provided QuickCart OCI image under
`quickcart_image_x86/`. The pytest fixture extracts the image layers, copies
the seeded `quickcart` binary and `quickcart.db`, launches the API locally on
`http://127.0.0.1:8080/api/v1`, and then runs each black-box test against a
fresh database copy.

This keeps the tests reproducible and avoids requiring Docker during grading.

## Black Box Test Design

The suite covers the required categories from the assignment brief:

- Valid requests
- Invalid inputs
- Missing fields or missing headers
- Wrong data types or malformed values
- Boundary values such as zero quantities, large amounts, invalid ratings, and
  checkout limits

Representative passing scenarios include:

- Missing `X-Roll-Number` and `X-User-ID` headers are rejected
- Valid profile updates persist correctly
- Address updates only change allowed fields
- Product listing hides inactive products
- Valid coupons apply with the correct discount and cap
- GST is added once during checkout
- Delivered orders cannot be cancelled
- Loyalty points redeem correctly when enough points are available
- Review averages preserve decimal precision
- Support tickets allow only forward status transitions

## Execution Summary

Primary commands:

```bash
python -m pytest blackbox/tests
python -m pytest
```

Expected black-box outcome with the current QuickCart image:

- Passing conformance tests
- `xfail` entries for confirmed API bugs that violate the documentation

Current observed result:

- `python -m pytest blackbox/tests` -> `40 passed, 12 xfailed`

The `xfail` tests are intentional. They act as executable bug reports so the
suite can still run cleanly while documenting the live API defects.

## Bug Reports

### BB-01 Multiple Default Addresses Remain After Adding A New Default

- Endpoint tested: `POST /api/v1/addresses`
- Request:
  - Method: `POST`
  - URL: `/api/v1/addresses`
  - Headers: `X-Roll-Number`, `X-User-ID`
  - Body:

```json
{
  "label": "OTHER",
  "street": "98765 Default Switch Road",
  "city": "Pune",
  "pincode": "654321",
  "is_default": true
}
```

- Expected result: the new address becomes the only default address
- Actual result: the old default stays `true`, so the user ends up with multiple default addresses

### BB-02 Product Prices Drift From The Seeded Admin Data

- Endpoint tested: `GET /api/v1/products`
- Request:
  - Method: `GET`
  - URL: `/api/v1/products`
  - Headers: `X-Roll-Number`, `X-User-ID`
- Expected result: every listed product price matches the exact real price in the seeded data
- Actual result: several prices are rounded or shifted, for example products such as `8`, `10`, and `16`

### BB-03 Product Sort Order Is Ignored

- Endpoint tested: `GET /api/v1/products?sort=asc` and `GET /api/v1/products?sort=desc`
- Request:
  - Method: `GET`
  - URL: `/api/v1/products?sort=asc`
  - Headers: `X-Roll-Number`, `X-User-ID`
- Expected result: returned products are sorted by price ascending or descending
- Actual result: the returned order does not follow the requested sort

### BB-04 Add-To-Cart Accepts Zero And Negative Quantities

- Endpoint tested: `POST /api/v1/cart/add`
- Request:
  - Method: `POST`
  - URL: `/api/v1/cart/add`
  - Headers: `X-Roll-Number`, `X-User-ID`
  - Body examples:

```json
{"product_id": 1, "quantity": 0}
```

```json
{"product_id": 1, "quantity": -1}
```

- Expected result: both requests return `400`
- Actual result: the API accepts them

### BB-05 Cart Subtotals And Total Are Calculated Incorrectly

- Endpoint tested: `GET /api/v1/cart`
- Request:
  - Method: `GET`
  - URL: `/api/v1/cart`
  - Headers: `X-Roll-Number`, `X-User-ID`
- Setup:
  - Add product `1` with quantity `2`
  - Add product `3` with quantity `5`
- Expected result:
  - subtotal for product `1` = `240`
  - subtotal for product `3` = `200`
  - cart total = `440`
- Actual result: subtotals overflow and the cart total does not correctly include all items

### BB-06 Expired Coupons Are Accepted

- Endpoint tested: `POST /api/v1/coupon/apply`
- Request:
  - Method: `POST`
  - URL: `/api/v1/coupon/apply`
  - Headers: `X-Roll-Number`, `X-User-ID`
  - Body:

```json
{"coupon_code": "EXPIRED100"}
```

- Setup: cart total high enough to satisfy the minimum cart value
- Expected result: the API rejects the coupon because it is expired
- Actual result: the coupon is accepted and a discount is applied

### BB-07 Empty Carts Can Still Be Checked Out

- Endpoint tested: `POST /api/v1/checkout`
- Request:
  - Method: `POST`
  - URL: `/api/v1/checkout`
  - Headers: `X-Roll-Number`, `X-User-ID`
  - Body:

```json
{"payment_method": "CARD"}
```

- Expected result: `400` because the cart is empty
- Actual result: checkout succeeds

### BB-08 Wallet Payments Deduct More Than The Requested Amount

- Endpoint tested: `POST /api/v1/wallet/pay`
- Request:
  - Method: `POST`
  - URL: `/api/v1/wallet/pay`
  - Headers: `X-Roll-Number`, `X-User-ID`
  - Body:

```json
{"amount": 25}
```

- Expected result: the wallet balance decreases by exactly `25`
- Actual result: the balance drops by more than the requested amount

### BB-09 Invoice Total Does Not Match The Fresh Checkout Total

- Endpoint tested: `GET /api/v1/orders/{order_id}/invoice`
- Request:
  - Method: `GET`
  - URL: `/api/v1/orders/{order_id}/invoice`
  - Headers: `X-Roll-Number`, `X-User-ID`
- Setup: place a fresh one-item card order
- Expected result: the invoice total matches the checkout total exactly
- Actual result: the invoice total is higher than the checkout result for the same order

### BB-10 Cancelling A New Order Can Hang

- Endpoint tested: `POST /api/v1/orders/{order_id}/cancel`
- Request:
  - Method: `POST`
  - URL: `/api/v1/orders/{order_id}/cancel`
  - Headers: `X-Roll-Number`, `X-User-ID`
- Setup: place a fresh order and immediately cancel it
- Expected result: the API returns a normal cancellation response and restores stock
- Actual result: the request can hang until client timeout

### BB-11 Review Rating Validation Allows `0`

- Endpoint tested: `POST /api/v1/products/{product_id}/reviews`
- Request:
  - Method: `POST`
  - URL: `/api/v1/products/250/reviews`
  - Headers: `X-Roll-Number`, `X-User-ID`
  - Body:

```json
{"rating": 0, "comment": "bad"}
```

- Expected result: `400` because ratings must be between `1` and `5`
- Actual result: the review is accepted

### BB-12 Support Ticket Messages Are Truncated

- Endpoint tested: `POST /api/v1/support/ticket`
- Request:
  - Method: `POST`
  - URL: `/api/v1/support/ticket`
  - Headers: `X-Roll-Number`, `X-User-ID`
  - Body:

```json
{
  "subject": "Refund help",
  "message": "Need a refund because the delivered apples were bruised."
}
```

- Expected result: the full message is saved exactly as sent
- Actual result: the message is truncated in the stored ticket data

## Simple Conclusion

The Part 3 black-box suite now exercises the documented QuickCart API behavior
end to end. It also captures the currently reproducible API defects as
intentional `xfail` tests, so the repository includes both a runnable
conformance suite and executable bug reports.
