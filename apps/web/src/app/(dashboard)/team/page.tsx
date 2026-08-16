import { Metadata } from "next"
import { fetchTeamServer } from "@/lib/api-server"

export const metadata: Metadata = {
  title: "Equipe | KS FoodOps",
  description: "Gestão de Usuários e Permissões",
}

export default async function TeamPage() {
  const members = await fetchTeamServer()

  return (
    <div className="flex flex-col gap-6 p-6">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold tracking-tight">Equipe & Permissões</h1>
      </div>
      <div className="rounded-xl border border-white/10 bg-white/5 backdrop-blur-md p-6">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead className="border-b border-white/10 text-xs uppercase text-zinc-400">
              <tr>
                <th className="px-4 py-3">ID Usuário</th>
                <th className="px-4 py-3">Papel (Role)</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-white/5">
              {members.map((member) => (
                <tr key={member.id} className="hover:bg-white/5">
                  <td className="px-4 py-3 font-medium text-zinc-100 font-mono text-xs">{member.user_id}</td>
                  <td className="px-4 py-3">
                    <span className="inline-flex items-center rounded-full bg-blue-500/10 px-2 py-1 text-xs font-medium text-blue-400 uppercase">
                      {member.role}
                    </span>
                  </td>
                </tr>
              ))}
              {members.length === 0 && (
                <tr>
                  <td colSpan={2} className="px-4 py-8 text-center text-zinc-500">Nenhum membro cadastrado.</td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}
