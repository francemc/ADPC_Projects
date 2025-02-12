using MedicalSystem.Data;
using MedicalSystem.Models;
using Microsoft.EntityFrameworkCore;

namespace MedicalSystem.Repositories
{
    public class CheckupRepository : IRepository<Checkup>
    {
        private readonly MedicalContext _context;

        public CheckupRepository(MedicalContext context)
        {
            _context = context;
        }

        public async Task<IEnumerable<Checkup>> GetAllAsync()
        {
            return await _context.Checkups.Include(c => c.Patient).ToListAsync();
        }

        public async Task<Checkup> GetByIdAsync(int id)
        {
            return await _context.Checkups.Include(c => c.Patient)
                                          .FirstOrDefaultAsync(c => c.CheckupID == id);
        }

        public async Task AddAsync(Checkup checkup)
        {
            await _context.Checkups.AddAsync(checkup);
        }

        public async Task UpdateAsync(Checkup checkup)
        {
            _context.Checkups.Update(checkup);
        }

        public async Task DeleteAsync(int id)
        {
            var checkup = await _context.Checkups.FindAsync(id);
            if (checkup != null)
            {
                _context.Checkups.Remove(checkup);
            }
        }

        public async Task SaveAsync()
        {
            await _context.SaveChangesAsync();
        }
    }
}
