using MedicalSystem.Data;
using MedicalSystem.Models;
using Microsoft.EntityFrameworkCore;

namespace MedicalSystem.Repositories
{
    public class MedicalRecordRepository : IRepository<MedicalRecord>
    {
        private readonly MedicalContext _context;

        public MedicalRecordRepository(MedicalContext context)
        {
            _context = context;
        }

        public async Task<IEnumerable<MedicalRecord>> GetAllAsync()
        {
            return await _context.MedicalRecords.Include(m => m.Patient).ToListAsync();
        }

        public async Task<MedicalRecord> GetByIdAsync(int id)
        {
            return await _context.MedicalRecords.Include(m => m.Patient)
                                                .FirstOrDefaultAsync(m => m.Id == id);
        }

        public async Task AddAsync(MedicalRecord medicalRecord)
        {
            await _context.MedicalRecords.AddAsync(medicalRecord);
        }

        public async Task UpdateAsync(MedicalRecord medicalRecord)
        {
            _context.MedicalRecords.Update(medicalRecord);
        }

        public async Task DeleteAsync(int id)
        {
            var medicalRecord = await _context.MedicalRecords.FindAsync(id);
            if (medicalRecord != null)
            {
                _context.MedicalRecords.Remove(medicalRecord);
            }
        }

        public async Task SaveAsync()
        {
            await _context.SaveChangesAsync();
        }
    }
}
