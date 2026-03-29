import Navbar from '../components/landing/Navbar';
import HeroSection from '../components/landing/HeroSection';
import DedicationSection from '../components/landing/DedicationSection';
import TargetAudienceSection from '../components/landing/TargetAudienceSection';
import UsageExamplesSection from '../components/landing/UsageExamplesSection';
import DevelopersSection from '../components/landing/DevelopersSection';
import ContactSection from '../components/landing/ContactSection';
import Footer from '../components/landing/Footer';

export default function LandingPage() {
  return (
    <div className="w-full flex flex-col bg-slate-950 text-slate-50 selection:bg-emerald-500/30">
      <Navbar />
      <HeroSection />
      <TargetAudienceSection />
      <UsageExamplesSection />
      <DevelopersSection />
      <DedicationSection />
      <ContactSection />
      <Footer />
    </div>
  );
}
