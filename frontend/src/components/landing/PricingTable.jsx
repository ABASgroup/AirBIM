import { PricingCard } from "@landing/PricingCard";

const tariffs = [
  {
    id: 1,
    name: "Тариф А",
    desc: "Краткая справка, что это за тариф и кому он нужен.",
    price: "10000",
    features: [
      "Первое преимущество",
      "Второе преимущество",
      "Третье преимущество",
      "Четвертое преимущество",
    ],
  },
  {
    id: 2,
    name: "Тариф Б",
    desc: "Краткая справка, что это за тариф и кому он нужен.",
    price: "20000",
    features: [
      "Первое преимущество",
      "Второе преимущество",
      "Третье преимущество",
      "Четвертое преимущество",
    ],
    isFeatured: true,
  },

  {
    id: 3,
    name: "Тариф В",
    desc: "Краткая справка, что это за тариф и кому он нужен.",
    price: "30000",
    features: [
      "Первое преимущество",
      "Второе преимущество",
      "Третье преимущество",
      "Четвертое преимущество",
    ],
  },
];

export const PricingTable = () => {
  return (
    <div className="flex flex-wrap justify-center gap-5">
      {tariffs.map((tariff) => (
        <PricingCard
          key={tariff.id}
          tariff={tariff}
          isFeatured={tariff.isFeatured}
        />
      ))}
    </div>
  );
};