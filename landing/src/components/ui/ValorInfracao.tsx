/** Selo de enquadramento sugerido pela IA; a explicação fica no rodapé de cada página. */
export function SeloPreliminar() {
  return <span className="inline-flex items-center border border-current px-1.5 py-0.5 text-[11px] leading-none font-semibold">preliminar</span>
}

/** Valor de uma obrigação nos blocos: número, "por infração" e o selo "preliminar". `texto` vem pronto do plano. */
export function ValorInfracao({ texto, enquadrado, preliminar, className = 'text-[28px]' }: { texto: string; enquadrado: boolean; preliminar: boolean; className?: string }) {
  return <span className="flex flex-col gap-1">
    <span className={`font-bold whitespace-nowrap ${className}`}>{texto}</span>
    {enquadrado && <span className="flex min-h-5 flex-wrap items-center gap-x-2 gap-y-1 text-xs">por infração{preliminar && <SeloPreliminar />}</span>}
  </span>
}
