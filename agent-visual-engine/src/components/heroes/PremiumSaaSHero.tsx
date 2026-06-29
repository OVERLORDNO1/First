"use client";

import { motion } from "framer-motion";

export type PremiumSaaSHeroProps = {
  brandName?: string;
  eyebrow?: string;
  headline?: string;
  subheadline?: string;
  primaryCta?: string;
  secondaryCta?: string;
  proofPoints?: string[];
  metrics?: Array<{
    value: string;
    label: string;
  }>;
  productHighlights?: string[];
};

const defaults: Required<PremiumSaaSHeroProps> = {
  brandName: "Northwind",
  eyebrow: "Now in private beta",
  headline: "Ship product analytics your whole team actually trusts.",
  subheadline:
    "One source of truth for every metric, every release, every decision. No spreadsheets, no guesswork, no late-night data wrangling.",
  primaryCta: "Start free trial",
  secondaryCta: "Book a demo",
  proofPoints: ["SOC 2 Type II", "99.99% uptime", "Trusted by 2,400+ teams"],
  metrics: [
    { value: "4.2M", label: "Events / sec" },
    { value: "<40ms", label: "Query latency" },
    { value: "98%", label: "Retained teams" },
  ],
  productHighlights: ["Revenue", "Active users", "Conversion"],
};

/* ----------------------------------------------------------------------------
 * Shared presentational pieces (pure — no animation, no motion references).
 * Safe to reuse from both the animated and the fully static hero.
 * ------------------------------------------------------------------------- */

function BrandMark({ brandName }: { brandName: string }) {
  return (
    <div className="flex items-center gap-2.5">
      <span className="grid h-7 w-7 place-items-center rounded-md border border-white/10 bg-white/5">
        <span className="h-2.5 w-2.5 rounded-sm bg-teal-300" />
      </span>
      <span className="text-sm font-medium tracking-tight text-neutral-200">{brandName}</span>
    </div>
  );
}

function Eyebrow({ eyebrow }: { eyebrow: string }) {
  return (
    <div className="inline-flex items-center gap-2 rounded-full border border-white/10 bg-white/[0.03] px-3 py-1 text-xs text-neutral-400 backdrop-blur-md">
      <span className="h-1.5 w-1.5 rounded-full bg-teal-300" />
      <span className="tracking-tight">{eyebrow}</span>
    </div>
  );
}

function ProofRow({ proofPoints }: { proofPoints: string[] }) {
  return (
    <ul className="flex flex-wrap items-center gap-x-5 gap-y-2 text-xs text-neutral-500">
      {proofPoints.map((point) => (
        <li key={point} className="flex items-center gap-2">
          <span className="h-1 w-1 rounded-full bg-neutral-600" />
          <span className="tracking-tight">{point}</span>
        </li>
      ))}
    </ul>
  );
}

function MetricCards({
  metrics,
}: {
  metrics: Array<{ value: string; label: string }>;
}) {
  return (
    <div className="grid grid-cols-3 gap-3">
      {metrics.map((metric) => (
        <div
          key={metric.label}
          className="rounded-xl border border-white/5 bg-white/[0.02] p-4 backdrop-blur-md"
        >
          <div className="text-xl font-semibold tracking-tight text-neutral-100 md:text-2xl">
            {metric.value}
          </div>
          <div className="mt-1 text-[11px] leading-tight tracking-tight text-neutral-500">
            {metric.label}
          </div>
        </div>
      ))}
    </div>
  );
}

function CtaButtons({
  primaryCta,
  secondaryCta,
}: {
  primaryCta: string;
  secondaryCta: string;
}) {
  return (
    <div className="flex flex-col gap-3 sm:flex-row">
      <button
        type="button"
        className="rounded-lg bg-teal-300 px-5 py-2.5 text-sm font-semibold tracking-tight text-neutral-950 transition-colors hover:bg-teal-200"
      >
        {primaryCta}
      </button>
      <button
        type="button"
        className="rounded-lg border border-white/10 bg-white/[0.03] px-5 py-2.5 text-sm font-medium tracking-tight text-neutral-200 transition-colors hover:bg-white/[0.07]"
      >
        {secondaryCta}
      </button>
    </div>
  );
}

/**
 * Faux product window built entirely from divs + Tailwind.
 * No images, no SVG, no icon packages, no remote assets.
 */
function ProductMockup({ productHighlights }: { productHighlights: string[] }) {
  const bars = [
    { id: "mon", h: 38 },
    { id: "tue", h: 56 },
    { id: "wed", h: 44 },
    { id: "thu", h: 72 },
    { id: "fri", h: 60 },
    { id: "sat", h: 88 },
    { id: "sun", h: 67 },
  ];
  const accentBar = bars.length - 2;

  return (
    <div className="overflow-hidden rounded-2xl border border-white/10 bg-neutral-900/60 shadow-2xl shadow-black/40 backdrop-blur-md">
      {/* chrome bar */}
      <div className="flex items-center gap-2 border-b border-white/5 px-4 py-3">
        <span className="h-2.5 w-2.5 rounded-full bg-neutral-700" />
        <span className="h-2.5 w-2.5 rounded-full bg-neutral-700" />
        <span className="h-2.5 w-2.5 rounded-full bg-neutral-700" />
        <div className="ml-3 h-5 flex-1 rounded-md border border-white/5 bg-white/[0.02]" />
      </div>

      {/* body */}
      <div className="space-y-4 p-4 sm:p-5">
        {/* highlight rows with status pills */}
        <div className="space-y-2">
          {productHighlights.map((label, i) => (
            <div
              key={label}
              className="flex items-center justify-between rounded-lg border border-white/5 bg-white/[0.02] px-3 py-2.5"
            >
              <div className="flex items-center gap-2.5">
                <span className="h-6 w-6 rounded-md border border-white/5 bg-white/[0.03]" />
                <span className="text-xs tracking-tight text-neutral-300">{label}</span>
              </div>
              <span
                className={`rounded-full px-2 py-0.5 text-[10px] font-medium tracking-tight ${
                  i === 1 ? "bg-teal-300/10 text-teal-200" : "bg-white/5 text-neutral-400"
                }`}
              >
                {i === 1 ? "Live" : "Stable"}
              </span>
            </div>
          ))}
        </div>

        {/* faux chart made of divs */}
        <div className="rounded-xl border border-white/5 bg-white/[0.02] p-4">
          <div className="mb-3 flex items-center justify-between">
            <div className="h-2 w-20 rounded-full bg-white/10" />
            <div className="h-2 w-10 rounded-full bg-white/5" />
          </div>
          <div className="flex h-24 items-end gap-2">
            {bars.map((bar, i) => (
              <div
                key={bar.id}
                style={{ height: `${bar.h}%` }}
                className={`flex-1 rounded-t-sm ${
                  i === accentBar ? "bg-teal-300/70" : "bg-white/10"
                }`}
              />
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

/* ----------------------------------------------------------------------------
 * Static hero — fully static. Zero references to Framer Motion, no animation
 * logic, no shared motion wrappers. Copy-paste usable without framer-motion.
 * ------------------------------------------------------------------------- */

export function PremiumSaaSHeroStatic(props: PremiumSaaSHeroProps) {
  const {
    brandName,
    eyebrow,
    headline,
    subheadline,
    primaryCta,
    secondaryCta,
    proofPoints,
    metrics,
    productHighlights,
  } = { ...defaults, ...props };

  return (
    <section className="relative w-full overflow-hidden bg-[#07070a] text-neutral-100">
      {/* ambient backdrop */}
      <div className="pointer-events-none absolute inset-0">
        <div className="absolute left-1/2 top-[-10%] h-[420px] w-[420px] -translate-x-1/2 rounded-full bg-teal-400/[0.06] blur-[120px]" />
        <div className="absolute inset-0 bg-[radial-gradient(circle_at_top,rgba(255,255,255,0.04),transparent_55%)]" />
      </div>

      <div className="relative mx-auto w-full max-w-6xl px-6 py-16 sm:py-20 lg:py-28">
        <header className="mb-12 flex items-center justify-between">
          <BrandMark brandName={brandName} />
          <span className="text-xs tracking-tight text-neutral-500">Sign in</span>
        </header>

        <div className="grid grid-cols-1 gap-12 lg:grid-cols-12 lg:items-center">
          {/* content — ~60% */}
          <div className="flex flex-col gap-6 lg:col-span-7">
            <div>
              <Eyebrow eyebrow={eyebrow} />
            </div>
            <h1 className="text-balance text-3xl font-semibold leading-[1.05] tracking-tight text-neutral-50 sm:text-5xl md:text-6xl">
              {headline}
            </h1>
            <p className="max-w-xl text-pretty text-base leading-relaxed tracking-tight text-neutral-400 sm:text-lg">
              {subheadline}
            </p>
            <CtaButtons primaryCta={primaryCta} secondaryCta={secondaryCta} />
            <div className="pt-2">
              <ProofRow proofPoints={proofPoints} />
            </div>
            <div className="pt-4">
              <MetricCards metrics={metrics} />
            </div>
          </div>

          {/* mockup — ~40% */}
          <div className="lg:col-span-5">
            <ProductMockup productHighlights={productHighlights} />
          </div>
        </div>
      </div>
    </section>
  );
}

/* ----------------------------------------------------------------------------
 * Animated hero — subtle entrance + micro-interactions via Framer Motion.
 * ------------------------------------------------------------------------- */

const ease = [0.16, 1, 0.3, 1] as const;

export function PremiumSaaSHero(props: PremiumSaaSHeroProps) {
  const {
    brandName,
    eyebrow,
    headline,
    subheadline,
    primaryCta,
    secondaryCta,
    proofPoints,
    metrics,
    productHighlights,
  } = { ...defaults, ...props };

  const container = {
    hidden: {},
    show: {
      transition: { staggerChildren: 0.08, delayChildren: 0.05 },
    },
  };

  const item = {
    hidden: { opacity: 0, y: 16 },
    show: { opacity: 1, y: 0, transition: { duration: 0.6, ease } },
  };

  return (
    <section className="relative w-full overflow-hidden bg-[#07070a] text-neutral-100">
      {/* ambient backdrop */}
      <div className="pointer-events-none absolute inset-0">
        <div className="absolute left-1/2 top-[-10%] h-[420px] w-[420px] -translate-x-1/2 rounded-full bg-teal-400/[0.06] blur-[120px]" />
        <div className="absolute inset-0 bg-[radial-gradient(circle_at_top,rgba(255,255,255,0.04),transparent_55%)]" />
      </div>

      <div className="relative mx-auto w-full max-w-6xl px-6 py-16 sm:py-20 lg:py-28">
        <motion.header
          initial={{ opacity: 0, y: -8 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, ease }}
          className="mb-12 flex items-center justify-between"
        >
          <BrandMark brandName={brandName} />
          <span className="text-xs tracking-tight text-neutral-500">Sign in</span>
        </motion.header>

        <div className="grid grid-cols-1 gap-12 lg:grid-cols-12 lg:items-center">
          {/* content — ~60% */}
          <motion.div
            variants={container}
            initial="hidden"
            animate="show"
            className="flex flex-col gap-6 lg:col-span-7"
          >
            <motion.div variants={item}>
              <Eyebrow eyebrow={eyebrow} />
            </motion.div>
            <motion.h1
              variants={item}
              className="text-balance text-3xl font-semibold leading-[1.05] tracking-tight text-neutral-50 sm:text-5xl md:text-6xl"
            >
              {headline}
            </motion.h1>
            <motion.p
              variants={item}
              className="max-w-xl text-pretty text-base leading-relaxed tracking-tight text-neutral-400 sm:text-lg"
            >
              {subheadline}
            </motion.p>
            <motion.div variants={item} className="flex flex-col gap-3 sm:flex-row">
              <motion.button
                type="button"
                whileHover={{ y: -1 }}
                whileTap={{ scale: 0.98 }}
                className="rounded-lg bg-teal-300 px-5 py-2.5 text-sm font-semibold tracking-tight text-neutral-950 transition-colors hover:bg-teal-200"
              >
                {primaryCta}
              </motion.button>
              <motion.button
                type="button"
                whileHover={{ y: -1 }}
                whileTap={{ scale: 0.98 }}
                className="rounded-lg border border-white/10 bg-white/[0.03] px-5 py-2.5 text-sm font-medium tracking-tight text-neutral-200 transition-colors hover:bg-white/[0.07]"
              >
                {secondaryCta}
              </motion.button>
            </motion.div>
            <motion.div variants={item} className="pt-2">
              <ProofRow proofPoints={proofPoints} />
            </motion.div>
            <motion.div variants={item} className="pt-4">
              <MetricCards metrics={metrics} />
            </motion.div>
          </motion.div>

          {/* mockup — ~40% */}
          <motion.div
            initial={{ opacity: 0, y: 24, scale: 0.98 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            transition={{ duration: 0.7, ease, delay: 0.15 }}
            className="lg:col-span-5"
          >
            <ProductMockup productHighlights={productHighlights} />
          </motion.div>
        </div>
      </div>
    </section>
  );
}
