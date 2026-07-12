import test from "node:test";
import assert from "node:assert/strict";
import {
  calculateContractCount,
  calculateContractProfit,
  calculateLiquidationPrice,
  calculateMaxPosition,
  calculateTargetClosePrice,
} from "/Users/charles/Desktop/folder/work/uaec-react-h5/src/pages/ContractPage/contractCalculatorMath.ts";

const base = {
  openPrice: "100",
  closePrice: "110",
  quantity: "2",
  leverage: "10",
  openMakerRate: "0.0002",
  openTakerRate: "0.0005",
};

test("long profit follows Android formula and formatting", () => {
  assert.deepEqual(calculateContractProfit({ ...base, side: "long" }), {
    margin: "20.00",
    profit: "20.00",
    returnRate: "100.00",
    makerFee: "-0.0040",
    takerFee: "-0.0100",
  });
});

test("short profit reverses price delta", () => {
  assert.deepEqual(calculateContractProfit({ ...base, side: "short" }), {
    margin: "20.00",
    profit: "-20.00",
    returnRate: "-100.00",
    makerFee: "-0.0040",
    takerFee: "-0.0100",
  });
});

test("tiny decimal inputs never stringify in scientific notation", () => {
  assert.deepEqual(
    calculateContractProfit({
      side: "long",
      openPrice: "0.00001234",
      closePrice: "0.00001235",
      quantity: "100000",
      leverage: "3",
      openMakerRate: "0.0002",
      openTakerRate: "0.0005",
    }),
    {
      margin: "0.41",
      profit: "0.00",
      returnRate: "0.24",
      makerFee: "-0.0001",
      takerFee: "-0.0002",
    },
  );
});

test("target close price supports amount mode for both sides", () => {
  assert.equal(calculateTargetClosePrice({ side: "long", mode: "amount", openPrice: "100", quantity: "2", leverage: "10", target: "20" }), "110.00");
  assert.equal(calculateTargetClosePrice({ side: "short", mode: "amount", openPrice: "100", quantity: "2", leverage: "10", target: "20" }), "90.00");
});

test("target close price supports Android return-rate sequence", () => {
  assert.equal(calculateTargetClosePrice({ side: "long", mode: "rate", openPrice: "100", quantity: "2", leverage: "10", target: "50" }), "105.00");
  assert.equal(calculateTargetClosePrice({ side: "short", mode: "rate", openPrice: "100", quantity: "2", leverage: "10", target: "50" }), "95.00");
});

test("invalid and zero divisors are rejected rather than silently coerced", () => {
  assert.throws(() => calculateContractProfit({ ...base, leverage: "0", side: "long" }), /leverage/);
  assert.throws(() => calculateTargetClosePrice({ side: "long", mode: "amount", openPrice: "100", quantity: "0", leverage: "10", target: "20" }), /quantity/);
  assert.throws(() => calculateTargetClosePrice({ side: "long", mode: "rate", openPrice: "abc", quantity: "2", leverage: "10", target: "20" }), /openPrice/);
});

const liquidationTiers = [
  { enableNum: "100", minMarginRate: "0.004" },
  { enableNum: "1000", minMarginRate: "0.01" },
];

function liquidation(overrides = {}) {
  return calculateLiquidationPrice({
    mode: "isolated",
    side: "long",
    openPrice: "100",
    quantity: "10",
    marginAmount: "20",
    leverage: "10",
    faceValue: "1",
    flatMakerFeeRate: "0.0002",
    flatTakerFeeRate: "0.0005",
    tiers: liquidationTiers,
    ...overrides,
  });
}

test("isolated long follows Android calculate3 sequence", () => {
  assert.deepEqual(liquidation(), {
    status: "calculated",
    price: "88.40",
    maintenanceMarginRate: "0.004",
  });
});

test("isolated short follows Android calculate3 sequence", () => {
  assert.deepEqual(liquidation({ side: "short" }), {
    status: "calculated",
    price: "111.50",
    maintenanceMarginRate: "0.004",
  });
});

test("cross long returns a calculated price below Android quantity guard", () => {
  assert.deepEqual(liquidation({ mode: "cross", openPrice: "5" }), {
    status: "calculated",
    price: "3.01",
    maintenanceMarginRate: "0.004",
  });
});

test("cross short returns a calculated price above Android quantity guard", () => {
  assert.deepEqual(liquidation({ mode: "cross", side: "short", openPrice: "20" }), {
    status: "calculated",
    price: "21.90",
    maintenanceMarginRate: "0.004",
  });
});

test("cross mode preserves Android unable-to-calculate guards", () => {
  assert.deepEqual(liquidation({ mode: "cross" }), {
    status: "unavailable",
    maintenanceMarginRate: "0.004",
  });
  assert.deepEqual(liquidation({ mode: "cross", side: "short", openPrice: "5" }), {
    status: "unavailable",
    maintenanceMarginRate: "0.004",
  });
});

test("isolated non-positive liquidation result is clamped to zero", () => {
  assert.deepEqual(liquidation({ leverage: "1", marginAmount: "0" }), {
    status: "calculated",
    price: "0.00",
    maintenanceMarginRate: "0.004",
  });
});

test("quantity-to-face-value selects the smallest eligible tier", () => {
  assert.deepEqual(liquidation({ side: "short", quantity: "200" }), {
    status: "calculated",
    price: "108.96",
    maintenanceMarginRate: "0.01",
  });
});

test("liquidation rejects missing tiers and a quantity beyond all tiers", () => {
  assert.throws(() => liquidation({ tiers: [] }), /tiers/);
  assert.throws(() => liquidation({ quantity: "1001" }), /eligible tier/);
});

test("max position follows Android leverage-tier selection", () => {
  const tiers = [
    { enableNum: "90", maxLever: "125" },
    { enableNum: "100", maxLever: "83.33333333" },
    { enableNum: "200", maxLever: "62.5" },
  ];
  assert.equal(calculateMaxPosition("84", "0.001", tiers), "0.0900");
  assert.equal(calculateMaxPosition("80", "0.001", tiers), "0.1000");
  assert.throws(() => calculateMaxPosition("126", "0.001", tiers), /leverage/);
});

test("contract count uses Android scale-5 then round-2 sequence", () => {
  assert.equal(calculateContractCount("1", "0.003"), "333.33");
  assert.equal(calculateContractCount("0.00000001", "0.00000003"), "0.33");
});

test("runtime discriminants are rejected instead of silently selecting another branch", () => {
  assert.throws(
    () => calculateContractProfit({ ...base, side: "invalid" }),
    /side/,
  );
  assert.throws(
    () => calculateTargetClosePrice({
      side: "long",
      mode: "invalid",
      openPrice: "100",
      quantity: "2",
      leverage: "10",
      target: "20",
    }),
    /mode/,
  );
  assert.throws(() => liquidation({ side: "invalid" }), /side/);
  assert.throws(() => liquidation({ mode: "invalid" }), /mode/);
});

test("all leverage-aware formulas reject values outside Android 1 through 125", () => {
  for (const leverage of ["0.5", "126"]) {
    assert.throws(
      () => calculateContractProfit({ ...base, leverage, side: "long" }),
      /leverage/,
    );
    assert.throws(
      () => calculateTargetClosePrice({
        side: "long",
        mode: "rate",
        openPrice: "100",
        quantity: "2",
        leverage,
        target: "20",
      }),
      /leverage/,
    );
    assert.throws(() => liquidation({ leverage }), /leverage/);
    assert.throws(
      () => calculateMaxPosition(leverage, "0.001", [
        { enableNum: "90", maxLever: "125" },
      ]),
      /leverage/,
    );
  }
});
