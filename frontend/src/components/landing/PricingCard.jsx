import { UnfilledButton } from "../UnfilledButton";

export const PricingCard = ({ tariff, isFeatured }) => {
  return (
    <div className={`relative flex flex-col items-center p-6 rounded-lg transition-all bg-surface text-main-purple w-80
      ${isFeatured ? "border-3 border-main-purple" : "none"}
    `}>
      {isFeatured && (
        <div className="absolute -top-4 bg-main-purple text-main-dark text-sm px-4 py-1 rounded-full">
          Особое предложение
        </div>
      )}

      <h3 className="text-3xl font-bold mb-4 mt-4">{tariff.name}</h3>

      <p>{tariff.desc}</p>

      <ul className="text-md text-main-white space-y-2 mb-5 list-disc">
        {tariff.features.map((feature, index) => (
          <li key={index} className="">
            <span className="text-main-white"></span> {feature}
          </li>
        ))}
      </ul>

      <p className="text-2xl mb-6 text-main-purple">
        {tariff.price} ₽
        <span className="text-sm text-main-white">/месяц</span>
      </p>
      <UnfilledButton color="purple">Выбрать</UnfilledButton>
    </div>
  );
};