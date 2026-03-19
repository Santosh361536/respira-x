import NavigationDock from '@/components/NavigationDock';
import CoughAnalyzer from '@/components/CoughAnalyzer';
import { DiagnoseButton } from '@/components/DiagnoseButton';
import { AnimatedGridPattern } from '@/components/ui/animated-grid-pattern';
import { FeatureGrid } from '@/components/ui/feature-grid';
import { cn } from '@/lib/utils';

const features = [
  {
    title: "CNN-Powered Analysis",
    description:
      "Utilizes advanced Convolutional Neural Networks (CNNs) to extract complex patterns from audio spectrograms for precise cough classification.",
  },
  {
    title: "Real-Time Processing",
    description:
      "Analyze audio inputs instantly, providing immediate feedback and diagnosis on respiratory health directly in your browser.",
  },
  {
    title: "Advanced Audio Extraction",
    description:
      "Leverages sophisticated audio processing techniques like MFCCs and Mel Spectrograms to convert sound waves into powerful diagnostic data.",
  },
  {
    title: "High Accuracy Classification",
    description:
      "Trained on extensive clinical datasets to accurately distinguish between various types of coughs, including dry, wet, and COVID-19 patterns.",
  },
  {
    title: "Secure Data Handling",
    description:
      "Ensures all audio recordings are processed securely, maintaining strict privacy and confidentiality of your sensitive health data.",
  },
  {
    title: "Detailed Health Insights",
    description:
      "Provides comprehensive visualizations and understandable reports of your respiratory analysis to keep you informed.",
  },
  {
    title: "Multi-Format Support",
    description:
      "Easily processes various audio formats — from WAV recordings to compressed MP3 files — without losing analytical fidelity.",
  },
  {
    title: "Scalable ML Architecture",
    description:
      "Built on a robust machine learning backend capable of handling high volumes of simultaneous analysis requests quickly and reliably.",
  },
];

const Index = () => {
  return (
    <div className="relative min-h-screen bg-background">
      {/* Hero Section */}
      <section id="hero" className="relative flex min-h-screen flex-col items-center justify-center overflow-hidden px-6">
        <AnimatedGridPattern
          numSquares={30}
          maxOpacity={0.1}
          duration={3}
          repeatDelay={1}
          className={cn(
            "[mask-image:radial-gradient(500px_circle_at_center,white,transparent)]",
            "inset-x-0 inset-y-[-30%] h-[200%] skew-y-12"
          )}
        />

        <div className="relative z-10 flex flex-col items-center text-center">
          <h1 className="font-bricolage text-5xl font-extrabold tracking-tighter sm:text-7xl text-foreground mt-[10vh]">
            RESPIRA-X
          </h1>
          <p className="mt-6 max-w-xl text-lg leading-relaxed text-muted-foreground">
            Breathe intelligence into respiratory health. Our platform uses deep learning and Convolutional Neural Networks to provide instant, accurate analysis of cough patterns.
          </p>

          <div className="mt-8">
            <DiagnoseButton />
          </div>

          <div className="mt-12">
            <NavigationDock />
          </div>
        </div>
      </section>

      {/* RESPIRA-X Section */}
      <section id="analyzer" className="relative py-24 px-6 z-20">
        <div className="mx-auto max-w-7xl">
          <CoughAnalyzer />
        </div>
      </section>

      {/* Features Section */}
      <section id="features" className="relative py-24 px-6 z-20">
        <div className="mx-auto max-w-7xl">
          <h2 className="font-bricolage text-3xl font-bold tracking-tight text-center text-foreground sm:text-4xl mb-16">
            Advanced Cough Analysis Features
          </h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-2">
            {features.map((feature, i) => (
              <div
                key={feature.title}
                className={cn(
                  "group/feature relative flex flex-col py-10 lg:border-r border-border",
                  i === 0 || i === 4 ? "lg:border-l" : "",
                  i < 4 ? "lg:border-b" : ""
                )}
              >
                <FeatureGrid />
                <div className="mb-4 relative z-10 px-10 text-muted-foreground">
                  <svg
                    xmlns="http://www.w3.org/2000/svg"
                    fill="none"
                    viewBox="0 0 24 24"
                    strokeWidth="1.5"
                    stroke="currentColor"
                    className="h-6 w-6"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      d="M3.75 13.5l10.5-11.25L12 10.5h8.25L9.75 21.75 12 13.5H3.75z"
                    />
                  </svg>
                </div>
                <div className="text-lg font-bold mb-2 relative z-10 px-10">
                  <div className="absolute left-0 inset-y-0 h-6 group-hover/feature:h-8 w-1 rounded-tr-full rounded-br-full bg-muted group-hover/feature:bg-primary transition-all duration-200 origin-center" />
                  <span className="group-hover/feature:translate-x-2 transition duration-200 inline-block text-foreground">
                    {feature.title}
                  </span>
                </div>
                <p className="text-sm text-muted-foreground max-w-xs relative z-10 px-10">
                  {feature.description}
                </p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* About Section */}
      <section id="about" className="relative py-24 px-6">
        <div className="mx-auto max-w-3xl text-center">
          <h2 className="font-bricolage text-3xl font-bold tracking-tight text-foreground sm:text-4xl mb-6">
            About the Project
          </h2>
          <p className="text-lg leading-relaxed text-muted-foreground">
            We are dedicated to building advanced diagnostic tools utilizing cutting-edge AI. By applying Convolutional Neural Networks to audio spectrograms, this analyzer was created to provide accessible, accurate, and rapid respiratory health insights directly from cough recordings.
          </p>
        </div>
      </section>
    </div>
  );
};

export default Index;
