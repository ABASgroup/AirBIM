import { LandingHeader } from "../components/landing/LandingHeader";
import { PromoTable } from "../components/landing/PromoTable";
import { PricingTable } from "../components/landing/PricingTable";

function LandingPage() {
  return (
    <>
      <LandingHeader />
      <main>
        <div className="flex flex-col items-center justify-center px-5 pt-5 text-center">
          <h1 className="text-primary-color text-4xl max-w-4xl leading-tight">
            Автоматизированный контроль строительных объектов на основе ИИ
          </h1>
          <p className="text-lg max-w-4xl mx-auto">
            <span className="text-text-color">Air</span>
            <span className="text-primary-color font-bold">BIM</span>{" "}
            автоматически находит отклонения реальности от проекта. 
            Сравнивайте облака точек с BIM-моделью и получайте готовые отчеты за считанные минуты.
          </p>
        </div>

        <div className="mt-20 max-w-7xl mx-auto">
          <PromoTable/>
        </div>

        <div className="mt-20">
          <PricingTable/>
        </div>
      </main>
    </>
  )
}

export default LandingPage