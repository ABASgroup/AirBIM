import { LandingHeader } from "../components/landing/LandingHeader";
import { PromoTable } from "../components/landing/PromoTable";
import { PricingTable } from "../components/landing/PricingTable";

function LandingPage() {
  return (
    <body>
      <LandingHeader />
      <main>
        <div className="flex flex-col items-center justify-center px-5 pt-5 text-center">
          <h1 className="text-main-purple text-4xl max-w-4xl leading-tight">
            Автоматизированный контроль строительных объектов на основе ИИ
          </h1>
          <p className="text-lg max-w-4xl mx-auto">
            <span className="text-main-white">Air</span>
            <span className="text-main-purple font-bold">BIM</span>{" "}
            автоматически находит отклонения реальности от проекта. 
            Сравнивайте облака точек с BIM-моделью и получайте готовые отчеты за считанные минуты.
          </p>
        </div>

        <div className="mt-20">
          <PromoTable/>
        </div>

        <div className="mt-20">
          <PricingTable/>
        </div>
      </main>
    </body>
  )
}

export default LandingPage