import { UnfilledButton } from "../ui/UnfilledButton";

export const PricingCard = ({ tariff, isFeatured }) => {
  return (
    <div className={`relative flex flex-col items-center p-6 rounded-lg transition-all bg-surface text-primary-color w-80
      ${isFeatured ? "border-3 border-primary-color" : "none"}
    `}>
      {isFeatured && (
        <div className="absolute -top-4 bg-primary-color text-background-color text-sm px-4 py-1 rounded-full">
          Особое предложение
        </div>
      )}

      <h3 className="text-3xl font-bold mb-4 mt-4">{tariff.name}</h3>

      <p>{tariff.desc}</p>

      <ul className="text-md text-text-color space-y-2 mb-5 list-disc">
        {tariff.features.map((feature, index) => (
          <li key={index} className="">
            <span className="text-text-color"></span> {feature}
          </li>
        ))}
      </ul>

      <p className="text-2xl mb-6 text-primary-color">
        {tariff.price} ₽
        <span className="text-sm text-text-color">/месяц</span>
      </p>
      <UnfilledButton color="purple">Выбрать</UnfilledButton>
    </div>
  );
};