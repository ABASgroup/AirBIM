// Таблица с промо приложения
import pic1 from "@/assets/images/landing/landing_pic1.png"
import pic2 from "@/assets/images/landing/landing_pic2.png"
import pic3 from "@/assets/images/landing/landing_pic3.png"
import pic4 from "@/assets/images/landing/landing_pic4.png"
import pic5 from "@/assets/images/landing/landing_pic5.png"

const steps = [
  {
    title: "Генерация облака точек",
    desc: "Вы загружаете проектную BIM-модель (IFC/Revit) и данные сканирования — облака точек в форматах .las или .laz. Система поддерживает данные как с LiDAR-сканеров, так и полученные методом фотограмметрии.",
    image: pic1,
    bgColor: "bg-background-color",
    textColor: "text-text-color"
  },
  {
    title: "Интеллектуальная обработка",
    desc: "ИИ-алгоритмы AirBIM автоматически очищают облако от «шумов»: строительной техники, временных лесов и людей. Система сегментирует данные, оставляя только конструктивные элементы здания.",
    image: pic2,
    bgColor: "bg-text-color",
    textColor: "text-background-color"
  },
  {
    title: "Автоматическое сопоставление",
    desc: "Сервис накладывает реальное облако точек на цифровую модель. Благодаря собственному модулю обработки, AirBIM с высокой точностью сопоставляет факт с планом.",
    image: pic3,
    bgColor: "bg-background-color",
    textColor: "text-text-color"
  },
  {
    title: "Анализ отклонений",
    desc: "Система автоматически выявляет любые расхождения геометрии: смещение стен, колонн или перекрытий. Вы видите распределение отклонений в метрах прямо на 3D-модели.",
    image: pic4,
    bgColor: "bg-text-color",
    textColor: "text-background-color"
  },
  {
    title: "Моментальная отчетность",
    desc: "На основе сопоставления AirBIM формирует отчет о строительных отклонениях и фиксирует реальный прогресс работ. Вы получаете готовую документацию для принятия решений без ручной рутины.",
    image: pic5,
    bgColor: "bg-background-color",
    textColor: "text-text-color"
  },
];

const StepSection = ({ step, index }) => {
  const isEven = index % 2 === 0;

  return (
    <section className={`${step.bgColor} ${step.textColor} overflow-hidden`}>
      <div className={`max-w-6xl h-80 flex flex-row items-center gap-12 ${isEven ? "" : "flex-row-reverse"} ${isEven ? "ml-auto" : "mr-auto"}`}>

        <div className="flex-1 space-y-5 items-center text-center">
          <h2 className={`text-4xl font-extrabold leading-tight ${step.textColor}`}>
            {step.title}
          </h2>
          <p className={`text-md max-w-xl mx-auto ${step.textColor}`}>
            {step.desc}
          </p>
        </div>
        <div className="flex-1 relative h-full w-full">
          <img
            src={step.image}
            alt={step.title}
            className="w-full h-full object-cover transition-all"
            style={{
              maskImage: `linear-gradient(${isEven ? "to right" : "to left"}, transparent 0%, black 25%)`,
            }}
          />
          <div
            className={`absolute inset-0 pointer-events-none bg-gradient-to-${isEven ? "l" : "r"} from-background-color via-transparent to-transparent`}
          />
        </div>
      </div>


    </section>
  );
};

export function PromoTable() {
  return (
    <div>
      {steps.map((step, index) => (
        <StepSection key={index} step={step} index={index} />
      ))}
    </div>
  );
}