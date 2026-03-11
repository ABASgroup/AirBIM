export const Input = ({...props}) => (
  <input
    className={`w-full bg-main-dark rounded-[5px] p-4 py-3 border-none box-border
      text-main-white placeholder:text-main-gray focus:bg-light-dark`}
    {...props}
  />
);