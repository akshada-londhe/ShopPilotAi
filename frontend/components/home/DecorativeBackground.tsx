export function DecorativeBackground() {
  return (
    <div aria-hidden className="pointer-events-none absolute inset-0 overflow-hidden">
      <div className="absolute -left-32 top-[290px] h-[330px] w-[330px] rounded-full bg-gradient-to-br from-[#f8e9ff] via-[#eeeaff] to-[#dce8ff] opacity-70 blur-[2px]" />
      <div className="absolute -right-36 top-[250px] h-[350px] w-[350px] rounded-full bg-gradient-to-br from-[#f6e9ff] via-[#eeeaff] to-[#dbe8ff] opacity-70 blur-[2px]" />
      <div className="absolute left-[10%] top-[385px] text-4xl text-[#ef8fca]">✦</div>
      <div className="absolute right-[10%] top-[450px] text-4xl text-[#efa1d4]">✦</div>
    </div>
  );
}