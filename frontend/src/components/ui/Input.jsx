export const Input = ({...props}) => (
  <input
    className={`w-full bg-background-color rounded-[5px] p-4 py-3 border-none box-border
      text-text-color placeholder:text-mute-text-color focus:bg-surface`}
    {...props}
  />
);