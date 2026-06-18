'use client'

import Link from 'next/link'
import { useSession } from 'next-auth/react'
import { useRouter } from 'next/navigation'
import { useEffect } from 'react'

export default function HomePage() {
  const { data: session, status } = useSession()
  const router = useRouter()

  useEffect(() => {
    if (status !== 'loading' && session) {
      router.push('/dashboard')
    }
  }, [session, status, router])

  return (
    <div className="min-h-screen" style={{ background: 'var(--off-white)' }}>
      {/* Hero Section - Asymmetric Editorial Layout */}
      <div className="relative overflow-hidden grain-texture">
        {/* Geometric Accent Elements */}
        <div className="absolute top-0 right-0 w-[600px] h-[600px] opacity-[0.03]"
             style={{
               background: `radial-gradient(circle, var(--cyan-electric) 0%, transparent 70%)`,
               transform: 'translate(30%, -30%)'
             }}
        />
        <div className="absolute bottom-0 left-0 w-[400px] h-[400px] opacity-[0.02]"
             style={{
               background: `radial-gradient(circle, var(--coral-warm) 0%, transparent 70%)`,
               transform: 'translate(-30%, 30%)'
             }}
        />

        <div className="max-w-7xl mx-auto px-6 lg:px-12 pt-32 pb-40">
          {/* Eyebrow - Animated */}
          <div className="reveal-up reveal-delay-1 mb-8">
            <div className="inline-flex items-center gap-3 px-4 py-2 rounded-full border"
                 style={{
                   borderColor: 'var(--cool-gray)',
                   background: 'rgba(255, 255, 255, 0.6)',
                   backdropFilter: 'blur(10px)'
                 }}>
              <div className="relative flex h-2 w-2">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full opacity-75"
                      style={{ background: 'var(--cyan-electric)' }} />
                <span className="relative inline-flex rounded-full h-2 w-2"
                      style={{ background: 'var(--cyan-electric)' }} />
              </div>
              <span className="font-mono text-xs tracking-wide uppercase"
                    style={{ color: 'var(--navy-mid)' }}>
                AI × Human Intelligence
              </span>
            </div>
          </div>

          {/* Main Headline - Asymmetric Grid */}
          <div className="grid lg:grid-cols-12 gap-12 items-start">
            <div className="lg:col-span-7">
              <h1 className="reveal-up reveal-delay-2 mb-6">
                <span className="block font-display text-6xl lg:text-7xl xl:text-8xl leading-[0.95] mb-4"
                      style={{ color: 'var(--navy-deep)' }}>
                  Intelligent
                </span>
                <span className="block font-display-light text-5xl lg:text-6xl xl:text-7xl leading-[0.95]"
                      style={{ color: 'var(--navy-mid)' }}>
                  Screening,
                </span>
                <span className="block font-display text-6xl lg:text-7xl xl:text-8xl leading-[0.95] mt-2"
                      style={{
                        background: `linear-gradient(135deg, var(--cyan-electric), var(--sage-green))`,
                        WebkitBackgroundClip: 'text',
                        WebkitTextFillColor: 'transparent',
                        backgroundClip: 'text'
                      }}>
                  Human Touch
                </span>
              </h1>

              <p className="reveal-up reveal-delay-3 text-xl lg:text-2xl leading-relaxed mb-10 max-w-xl"
                 style={{ color: 'var(--navy-light)' }}>
                AI analyzes candidates with precision. You make the final call.
                Save 93% of screening time while maintaining complete control.
              </p>

              {/* CTA */}
              <div className="reveal-up reveal-delay-4 flex flex-col sm:flex-row gap-4">
                <Link
                  href="/jobs"
                  className="group relative px-8 py-4 rounded-none font-medium text-lg overflow-hidden hover-lift"
                  style={{
                    background: 'var(--navy-deep)',
                    color: 'var(--off-white)',
                    boxShadow: 'var(--shadow-soft)'
                  }}
                >
                  <span className="relative z-10 flex items-center justify-center gap-2">
                    Explore Positions
                    <svg className="w-5 h-5 transition-transform group-hover:translate-x-1"
                         fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                            d="M17 8l4 4m0 0l-4 4m4-4H3" />
                    </svg>
                  </span>
                  <div className="absolute inset-0 opacity-0 group-hover:opacity-100 transition-opacity"
                       style={{ background: 'var(--navy-mid)' }} />
                </Link>

                <div className="flex items-center gap-3 px-6 py-4 font-mono text-sm"
                     style={{ color: 'var(--navy-mid)' }}>
                  <div className="w-px h-8" style={{ background: 'var(--cool-gray)' }} />
                  <span>No login required</span>
                </div>
              </div>
            </div>

            {/* Stats Panel - Offset */}
            <div className="lg:col-span-5 lg:mt-20">
              <div className="reveal-up reveal-delay-5 accent-line pl-6 space-y-8">
                <div>
                  <div className="font-display text-5xl mb-2"
                       style={{ color: 'var(--cyan-electric)' }}>
                    93%
                  </div>
                  <div className="text-sm uppercase tracking-wider font-medium"
                       style={{ color: 'var(--navy-mid)' }}>
                    Time Saved
                  </div>
                  <p className="mt-2 text-sm leading-relaxed"
                     style={{ color: 'var(--navy-light)' }}>
                    Automated CV analysis and screening questions reduce manual review time dramatically
                  </p>
                </div>

                <div>
                  <div className="font-display text-5xl mb-2"
                       style={{ color: 'var(--sage-green)' }}>
                    100%
                  </div>
                  <div className="text-sm uppercase tracking-wider font-medium"
                       style={{ color: 'var(--navy-mid)' }}>
                    Human Oversight
                  </div>
                  <p className="mt-2 text-sm leading-relaxed"
                     style={{ color: 'var(--navy-light)' }}>
                    Every decision requires human approval. AI recommends, you decide
                  </p>
                </div>

                <div>
                  <div className="font-display text-5xl mb-2"
                       style={{ color: 'var(--coral-warm)' }}>
                    24/7
                  </div>
                  <div className="text-sm uppercase tracking-wider font-medium"
                       style={{ color: 'var(--navy-mid)' }}>
                    Intelligent Response
                  </div>
                  <p className="mt-2 text-sm leading-relaxed"
                     style={{ color: 'var(--navy-light)' }}>
                    Automated scheduling and empathetic candidate communication around the clock
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* How It Works - Editorial Grid */}
      <div className="py-32" style={{ background: 'white' }}>
        <div className="max-w-7xl mx-auto px-6 lg:px-12">
          <div className="grid lg:grid-cols-12 gap-16">
            {/* Section Header */}
            <div className="lg:col-span-4">
              <div className="sticky top-32">
                <div className="font-mono text-xs uppercase tracking-wider mb-4"
                     style={{ color: 'var(--navy-mid)' }}>
                  Process
                </div>
                <h2 className="font-display text-4xl lg:text-5xl leading-tight"
                    style={{ color: 'var(--navy-deep)' }}>
                  How It Works
                </h2>
                <p className="mt-6 text-lg leading-relaxed"
                   style={{ color: 'var(--navy-light)' }}>
                  A seamless workflow that combines AI efficiency with human judgment
                </p>
              </div>
            </div>

            {/* Steps */}
            <div className="lg:col-span-8 space-y-16">
              {/* Step 1 */}
              <div className="group hover-lift p-8 rounded-none border-l-4"
                   style={{
                     borderColor: 'var(--cyan-electric)',
                     background: 'var(--off-white)',
                     boxShadow: 'var(--shadow-soft)'
                   }}>
                <div className="flex items-start gap-6">
                  <div className="flex-shrink-0 w-12 h-12 rounded-full flex items-center justify-center font-mono font-medium"
                       style={{
                         background: 'var(--cyan-electric)',
                         color: 'var(--navy-deep)'
                       }}>
                    01
                  </div>
                  <div className="flex-1">
                    <h3 className="font-display text-2xl mb-3"
                        style={{ color: 'var(--navy-deep)' }}>
                      Candidate Applies
                    </h3>
                    <p className="text-lg leading-relaxed"
                       style={{ color: 'var(--navy-light)' }}>
                      Simple application form. Upload resume, answer basic questions.
                      Our system immediately begins analysis.
                    </p>
                  </div>
                </div>
              </div>

              {/* Step 2 */}
              <div className="group hover-lift p-8 rounded-none border-l-4"
                   style={{
                     borderColor: 'var(--sage-green)',
                     background: 'var(--off-white)',
                     boxShadow: 'var(--shadow-soft)'
                   }}>
                <div className="flex items-start gap-6">
                  <div className="flex-shrink-0 w-12 h-12 rounded-full flex items-center justify-center font-mono font-medium"
                       style={{
                         background: 'var(--sage-green)',
                         color: 'var(--navy-deep)'
                       }}>
                    02
                  </div>
                  <div className="flex-1">
                    <h3 className="font-display text-2xl mb-3"
                        style={{ color: 'var(--navy-deep)' }}>
                      AI Analyzes & Scores
                    </h3>
                    <p className="text-lg leading-relaxed"
                       style={{ color: 'var(--navy-light)' }}>
                      Advanced LLM evaluates CV against your rubric, generates personalized
                      screening questions, and provides detailed scoring.
                    </p>
                  </div>
                </div>
              </div>

              {/* Step 3 */}
              <div className="group hover-lift p-8 rounded-none border-l-4"
                   style={{
                     borderColor: 'var(--coral-warm)',
                     background: 'var(--off-white)',
                     boxShadow: 'var(--shadow-soft)'
                   }}>
                <div className="flex items-start gap-6">
                  <div className="flex-shrink-0 w-12 h-12 rounded-full flex items-center justify-center font-mono font-medium"
                       style={{
                         background: 'var(--coral-warm)',
                         color: 'white'
                       }}>
                    03
                  </div>
                  <div className="flex-1">
                    <h3 className="font-display text-2xl mb-3"
                        style={{ color: 'var(--navy-deep)' }}>
                      You Make the Call
                    </h3>
                    <p className="text-lg leading-relaxed"
                       style={{ color: 'var(--navy-light)' }}>
                      Review AI recommendations with full context. Approve, reject, or request
                      more information. Complete control stays with you.
                    </p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Final CTA */}
      <div className="py-32 relative overflow-hidden"
           style={{ background: 'var(--navy-deep)' }}>
        <div className="absolute inset-0 opacity-10"
             style={{
               backgroundImage: `repeating-linear-gradient(
                 45deg,
                 transparent,
                 transparent 10px,
                 var(--cyan-electric) 10px,
                 var(--cyan-electric) 11px
               )`
             }}
        />
        <div className="relative max-w-4xl mx-auto px-6 lg:px-12 text-center">
          <h2 className="font-display text-4xl lg:text-5xl mb-6"
              style={{ color: 'var(--off-white)' }}>
            Ready to Transform Your Hiring?
          </h2>
          <p className="text-xl mb-10"
             style={{ color: 'var(--cool-gray)' }}>
            Join companies hiring smarter with AI-powered screening
          </p>
          <Link
            href="/jobs"
            className="inline-flex items-center gap-2 px-8 py-4 rounded-none font-medium text-lg hover-lift"
            style={{
              background: 'var(--cyan-electric)',
              color: 'var(--navy-deep)',
              boxShadow: 'var(--shadow-medium)'
            }}
          >
            View Open Positions
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                    d="M17 8l4 4m0 0l-4 4m4-4H3" />
            </svg>
          </Link>
        </div>
      </div>
    </div>
  )
}
